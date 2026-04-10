import os
from datetime import datetime
from functools import wraps

from flask import Blueprint, render_template, request, redirect, url_for, current_app, session, abort
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

from .db import get_db

bp = Blueprint("main", __name__)

# Configuration pour la sécurité des fichiers
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
MAX_CONTENT_LENGTH = 1000  # Limite de caractères pour les posts/bios


# -------------------------------------------------
# Helpers
# -------------------------------------------------

def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("main.connexion"))
        return view(*args, **kwargs)
    return wrapped_view


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_current_user():
    if "user_id" not in session:
        return None

    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE id = %s", (session["user_id"],))
        return cursor.fetchone()


def get_unread_notifications_count(user_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) AS unread_count
            FROM notifications
            WHERE user_id = %s
              AND is_read = 0
        """, (user_id,))
        return cursor.fetchone()["unread_count"]


def get_unread_messages_count(user_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) AS unread_count
            FROM messages
            WHERE receiver_id = %s
              AND is_read = 0
        """, (user_id,))
        return cursor.fetchone()["unread_count"]


@bp.app_context_processor
def inject_global_template_data():
    if "user_id" not in session:
        return {}

    current_user_id = session["user_id"]

    return {
        "current_user": get_current_user(),
        "unread_notifications_count": get_unread_notifications_count(current_user_id),
        "unread_messages_count": get_unread_messages_count(current_user_id),
    }


def format_time_ago(dt):
    if dt is None:
        return ""

    now = datetime.now(dt.tzinfo) if getattr(dt, "tzinfo", None) else datetime.now()
    diff = now - dt
    seconds = int(diff.total_seconds())

    if seconds < 60:
        return f"{seconds}s"

    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}min"

    hours = minutes // 60
    if hours < 24:
        return f"{hours}h"

    days = hours // 24
    if days < 7:
        return f"{days}j"

    weeks = days // 7
    if weeks < 5:
        return f"{weeks}sem"

    months = days // 30
    if months < 12:
        return f"{months}mo"

    years = days // 365
    return f"{years}a"


def format_full_datetime(dt):
    if dt is None:
        return ""

    months = {
        1: "janvier",
        2: "février",
        3: "mars",
        4: "avril",
        5: "mai",
        6: "juin",
        7: "juillet",
        8: "août",
        9: "septembre",
        10: "octobre",
        11: "novembre",
        12: "décembre"
    }

    return f"{dt.strftime('%H:%M')} · {dt.day} {months[dt.month]} {dt.year}"


# -------------------------------------------------
# Feed
# -------------------------------------------------

@bp.route("/")
@login_required
def feed():
    db = get_db()
    current_user_id = session["user_id"]

    with db.cursor() as cursor:
        cursor.execute("""
            SELECT
                posts.id,
                posts.user_id,
                posts.content,
                posts.media_url,
                posts.created_at,
                users.username,
                users.display_name,
                users.avatar_url,
                COUNT(DISTINCT likes.id) AS like_count,
                COUNT(DISTINCT replies.id) AS comment_count,
                EXISTS (
                    SELECT 1
                    FROM likes AS my_like
                    WHERE my_like.post_id = posts.id
                      AND my_like.user_id = %s
                ) AS liked_by_me
            FROM posts
            JOIN users ON users.id = posts.user_id
            LEFT JOIN likes ON likes.post_id = posts.id
            LEFT JOIN posts AS replies ON replies.reply_to_post_id = posts.id
            WHERE posts.reply_to_post_id IS NULL
            GROUP BY
                posts.id,
                posts.user_id,
                posts.content,
                posts.media_url,
                posts.created_at,
                users.username,
                users.display_name,
                users.avatar_url
            ORDER BY posts.created_at DESC
        """, (current_user_id,))
        raw_posts = cursor.fetchall()

        posts = []
        for row in raw_posts:
            post = dict(row)
            post["time_ago"] = format_time_ago(post["created_at"])

            cursor.execute("""
                SELECT
                    posts.id,
                    posts.user_id,
                    posts.content,
                    posts.created_at,
                    users.username,
                    users.display_name,
                    users.avatar_url
                FROM posts
                JOIN users ON users.id = posts.user_id
                WHERE posts.reply_to_post_id = %s
                ORDER BY posts.created_at DESC
                LIMIT 3
            """, (post["id"],))
            comments_preview = cursor.fetchall()

            post["comments_preview"] = []
            for comment in comments_preview:
                comment_dict = dict(comment)
                comment_dict["time_ago"] = format_time_ago(comment_dict["created_at"])
                post["comments_preview"].append(comment_dict)

            posts.append(post)

    return render_template(
    "home.html",
    posts=posts,
    show_publish_button=True
)


# -------------------------------------------------
# Ajout d'un post
# -------------------------------------------------

@bp.route("/add-post", methods=["POST"])
@login_required
def add_post():
    db = get_db()
    user_id = session["user_id"]
    username = session["username"]

    content = request.form.get("content", "").strip()
    media_file = request.files.get("media")

    if len(content) > MAX_CONTENT_LENGTH:
        return "Contenu trop long", 400

    if not content and not media_file:
        return redirect(request.referrer or url_for("main.feed"))

    with db.cursor() as cursor:
        cursor.execute("""
            INSERT INTO posts (user_id, content, media_url)
            VALUES (%s, %s, NULL)
        """, (user_id, content))

        post_id = cursor.lastrowid

        if media_file and media_file.filename != "" and allowed_file(media_file.filename):
            ext = media_file.filename.rsplit(".", 1)[-1].lower()
            new_filename = secure_filename(f"{username}_{post_id}_image.{ext}")

            upload_folder = os.path.join(current_app.root_path, "static", "img", "post")
            os.makedirs(upload_folder, exist_ok=True)

            media_file.save(os.path.join(upload_folder, new_filename))
            media_url = url_for("static", filename=f"img/post/{new_filename}")

            cursor.execute(
                "UPDATE posts SET media_url = %s WHERE id = %s",
                (media_url, post_id)
            )

    db.commit()
    return redirect(request.referrer or url_for("main.feed"))


# -------------------------------------------------
# Likes / Unlike
# -------------------------------------------------

@bp.route("/like/<int:post_id>", methods=["POST"])
@login_required
def like_post(post_id):
    db = get_db()
    user_id = session["user_id"]

    with db.cursor() as cursor:
        cursor.execute("""
            SELECT id
            FROM likes
            WHERE user_id = %s
              AND post_id = %s
        """, (user_id, post_id))
        already_liked = cursor.fetchone()

        if already_liked is None:
            cursor.execute("""
                INSERT INTO likes (user_id, post_id)
                VALUES (%s, %s)
            """, (user_id, post_id))

            cursor.execute("""
                SELECT user_id
                FROM posts
                WHERE id = %s
            """, (post_id,))
            post = cursor.fetchone()

            if post and post["user_id"] != user_id:
                cursor.execute("""
                    INSERT INTO notifications (user_id, sender_id, post_id, reply_id, type, is_read)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (post["user_id"], user_id, post_id, None, "like", 0))

        db.commit()

    return redirect(request.referrer or url_for("main.feed"))


@bp.route("/unlike/<int:post_id>", methods=["POST"])
@login_required
def unlike_post(post_id):
    db = get_db()
    user_id = session["user_id"]

    with db.cursor() as cursor:
        cursor.execute("""
            DELETE FROM likes
            WHERE user_id = %s
              AND post_id = %s
        """, (user_id, post_id))
        db.commit()

    return redirect(request.referrer or url_for("main.feed"))


# -------------------------------------------------
# Commentaires
# -------------------------------------------------

@bp.route("/comment/<int:post_id>", methods=["POST"])
@login_required
def add_comment(post_id):
    content = request.form.get("content", "").strip()

    if not content or len(content) > MAX_CONTENT_LENGTH:
        return redirect(request.referrer or url_for("main.feed"))

    db = get_db()
    current_user_id = session["user_id"]

    with db.cursor() as cursor:
        cursor.execute("""
            INSERT INTO posts (user_id, content, media_url, reply_to_post_id)
            VALUES (%s, %s, %s, %s)
        """, (current_user_id, content, None, post_id))

        reply_id = cursor.lastrowid

        cursor.execute("""
            SELECT user_id
            FROM posts
            WHERE id = %s
        """, (post_id,))
        parent_post = cursor.fetchone()

        if parent_post and parent_post["user_id"] != current_user_id:
            cursor.execute("""
                INSERT INTO notifications (user_id, sender_id, post_id, reply_id, type, is_read)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (parent_post["user_id"], current_user_id, post_id, reply_id, "reply", 0))

        db.commit()

    return redirect(request.referrer or url_for("main.feed"))


@bp.route("/delete-comment/<int:comment_id>", methods=["POST"])
@login_required
def delete_comment(comment_id):
    db = get_db()
    current_user_id = session["user_id"]

    with db.cursor() as cursor:
        cursor.execute("""
            SELECT id, user_id, reply_to_post_id
            FROM posts
            WHERE id = %s
        """, (comment_id,))
        comment = cursor.fetchone()

        if comment is None:
            abort(404)

        if comment["user_id"] != current_user_id:
            abort(403)

        if comment["reply_to_post_id"] is None:
            abort(400)

        cursor.execute("DELETE FROM posts WHERE id = %s", (comment_id,))
        db.commit()

    return redirect(request.referrer or url_for("main.feed"))


# -------------------------------------------------
# Affichage / Suppression post
# -------------------------------------------------

@bp.route("/post/<int:post_id>")
@login_required
def view_post(post_id):
    db = get_db()
    current_user_id = session["user_id"]

    with db.cursor() as cursor:
        cursor.execute("""
            SELECT
                posts.id,
                posts.user_id,
                posts.content,
                posts.media_url,
                posts.created_at,
                users.username,
                users.display_name,
                users.avatar_url,
                COUNT(DISTINCT likes.id) AS like_count,
                COUNT(DISTINCT replies.id) AS comment_count,
                EXISTS (
                    SELECT 1
                    FROM likes AS my_like
                    WHERE my_like.post_id = posts.id
                      AND my_like.user_id = %s
                ) AS liked_by_me
            FROM posts
            JOIN users ON users.id = posts.user_id
            LEFT JOIN likes ON likes.post_id = posts.id
            LEFT JOIN posts AS replies ON replies.reply_to_post_id = posts.id
            WHERE posts.id = %s
            GROUP BY
                posts.id,
                posts.user_id,
                posts.content,
                posts.media_url,
                posts.created_at,
                users.username,
                users.display_name,
                users.avatar_url
        """, (current_user_id, post_id))
        post = cursor.fetchone()

        if post is None:
            abort(404)

        post = dict(post)
        post["time_ago"] = format_time_ago(post["created_at"])
        post["full_created_at"] = format_full_datetime(post["created_at"])

        cursor.execute("""
            SELECT
                posts.id,
                posts.user_id,
                posts.content,
                posts.created_at,
                users.username,
                users.display_name,
                users.avatar_url
            FROM posts
            JOIN users ON users.id = posts.user_id
            WHERE posts.reply_to_post_id = %s
            ORDER BY posts.created_at ASC
        """, (post_id,))
        raw_comments = cursor.fetchall()

        comments = []
        for comment in raw_comments:
            comment_dict = dict(comment)
            comment_dict["time_ago"] = format_time_ago(comment_dict["created_at"])
            comment_dict["full_created_at"] = format_full_datetime(comment_dict["created_at"])
            comments.append(comment_dict)

    return render_template("view_post.html", post=post, comments=comments)


@bp.route("/delete-post/<int:post_id>", methods=["POST"])
@login_required
def delete_post(post_id):
    db = get_db()
    current_user_id = session["user_id"]

    with db.cursor() as cursor:
        cursor.execute("""
            SELECT id, user_id, reply_to_post_id
            FROM posts
            WHERE id = %s
        """, (post_id,))
        post = cursor.fetchone()

        if post is None:
            abort(404)

        if post["user_id"] != current_user_id:
            abort(403)

        if post["reply_to_post_id"] is not None:
            abort(400)

        cursor.execute("DELETE FROM posts WHERE id = %s", (post_id,))
        db.commit()

    return redirect(request.referrer or url_for("main.feed"))


# -------------------------------------------------
# Profil
# -------------------------------------------------

@bp.route("/profile/<username>")
@login_required
def profile(username):
    db = get_db()
    current_user_id = session["user_id"]

    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user is None:
            abort(404)

        cursor.execute("""
            SELECT 1
            FROM follows
            WHERE follower_id = %s
              AND following_id = %s
        """, (current_user_id, user["id"]))
        is_following = cursor.fetchone() is not None

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM follows
            WHERE following_id = %s
        """, (user["id"],))
        followers_count = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM follows
            WHERE follower_id = %s
        """, (user["id"],))
        following_count = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT
                posts.id,
                posts.user_id,
                posts.content,
                posts.media_url,
                posts.created_at,
                posts.reply_to_post_id,
                users.username,
                users.display_name,
                users.avatar_url,
                (SELECT COUNT(*) FROM likes WHERE post_id = posts.id) AS like_count,
                (SELECT COUNT(*) FROM posts AS p2 WHERE p2.reply_to_post_id = posts.id) AS comment_count,
                EXISTS (
                    SELECT 1
                    FROM likes
                    WHERE user_id = %s
                      AND post_id = posts.id
                ) AS liked_by_me
            FROM posts
            JOIN users ON posts.user_id = users.id
            WHERE posts.user_id = %s
              AND posts.reply_to_post_id IS NULL
            ORDER BY posts.created_at DESC
        """, (current_user_id, user["id"]))
        raw_posts = cursor.fetchall()

        posts = []
        for row in raw_posts:
            post = dict(row)
            post["time_ago"] = format_time_ago(post["created_at"])

            cursor.execute("""
                SELECT
                    posts.id,
                    posts.user_id,
                    posts.content,
                    posts.created_at,
                    users.username,
                    users.display_name,
                    users.avatar_url
                FROM posts
                JOIN users ON users.id = posts.user_id
                WHERE posts.reply_to_post_id = %s
                ORDER BY posts.created_at DESC
                LIMIT 3
            """, (post["id"],))
            comments_preview = cursor.fetchall()

            post["comments_preview"] = []
            for comment in comments_preview:
                comment_dict = dict(comment)
                comment_dict["time_ago"] = format_time_ago(comment_dict["created_at"])
                post["comments_preview"].append(comment_dict)

            posts.append(post)

    return render_template(
        "profil.html",
        user=user,
        posts=posts,
        is_following=is_following,
        followers_count=followers_count,
        following_count=following_count
    )


@bp.route("/edit-profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    db = get_db()
    current_user_id = session["user_id"]
    username = session["username"]

    if request.method == "POST":
        display_name = request.form.get("display_name", "").strip()
        bio = request.form.get("bio", "").strip()
        email = request.form.get("email", "").strip()

        if len(bio) > MAX_CONTENT_LENGTH or len(display_name) > 100:
            return "Entrée trop longue", 400

        avatar_file = request.files.get("avatar")
        banner_file = request.files.get("banner")

        with db.cursor() as cursor:
            cursor.execute("""
                UPDATE users
                SET display_name = %s, bio = %s, email = %s
                WHERE id = %s
            """, (display_name, bio, email, current_user_id))

            if avatar_file and avatar_file.filename != "" and allowed_file(avatar_file.filename):
                ext = avatar_file.filename.rsplit(".", 1)[-1].lower()
                avatar_filename = secure_filename(f"{username}_avatar.{ext}")
                upload_folder = os.path.join(current_app.root_path, "static", "img", "Avatar")
                os.makedirs(upload_folder, exist_ok=True)
                avatar_file.save(os.path.join(upload_folder, avatar_filename))
                cursor.execute("""
                    UPDATE users
                    SET avatar_url = %s
                    WHERE id = %s
                """, (avatar_filename, current_user_id))

            if banner_file and banner_file.filename != "" and allowed_file(banner_file.filename):
                ext = banner_file.filename.rsplit(".", 1)[-1].lower()
                banner_filename = secure_filename(f"{username}_banner.{ext}")
                upload_folder = os.path.join(current_app.root_path, "static", "img", "banniere")
                os.makedirs(upload_folder, exist_ok=True)
                banner_file.save(os.path.join(upload_folder, banner_filename))
                cursor.execute("""
                    UPDATE users
                    SET banner_url = %s
                    WHERE id = %s
                """, (banner_filename, current_user_id))

            db.commit()

        return redirect(url_for("main.profile", username=username))

    return render_template("edit_profil.html")


# -------------------------------------------------
# Follows
# -------------------------------------------------

@bp.route("/follow/<int:target_user_id>", methods=["POST"])
@login_required
def follow_user(target_user_id):
    current_user_id = session["user_id"]

    if current_user_id == target_user_id:
        return "Impossible de se suivre soi-même", 400

    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("""
            SELECT id
            FROM follows
            WHERE follower_id = %s
              AND following_id = %s
        """, (current_user_id, target_user_id))
        follow_rel = cursor.fetchone()

        if follow_rel:
            cursor.execute("""
                DELETE FROM follows
                WHERE follower_id = %s
                  AND following_id = %s
            """, (current_user_id, target_user_id))
        else:
            cursor.execute("""
                INSERT INTO follows (follower_id, following_id)
                VALUES (%s, %s)
            """, (current_user_id, target_user_id))

            cursor.execute("""
                INSERT INTO notifications (user_id, sender_id, post_id, reply_id, type, is_read)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (target_user_id, current_user_id, None, None, "follow", 0))

        db.commit()

    return redirect(request.referrer or url_for("main.profile", username=session["username"]))


@bp.route("/amis")
@login_required
def amis():
    db = get_db()
    user_id = session["user_id"]

    with db.cursor() as cursor:
        cursor.execute("""
            SELECT u.id, u.username, u.display_name, u.avatar_url, u.bio
            FROM users u
            JOIN follows f ON u.id = f.following_id
            WHERE f.follower_id = %s
        """, (user_id,))
        abonnements = cursor.fetchall()

        cursor.execute("""
            SELECT u.id, u.username, u.display_name, u.avatar_url, u.bio
            FROM users u
            JOIN follows f ON u.id = f.follower_id
            WHERE f.following_id = %s
        """, (user_id,))
        abonnes = cursor.fetchall()

    return render_template(
        "amis.html",
        abonnements=abonnements,
        abonnes=abonnes
    )


# -------------------------------------------------
# Connexion / Inscription
# -------------------------------------------------

@bp.route("/connexion", methods=["GET", "POST"])
def connexion():
    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        db = get_db()

        with db.cursor() as cursor:
            cursor.execute("""
                SELECT *
                FROM users
                WHERE username = %s
            """, (username,))
            user = cursor.fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("main.feed"))

        error = "Identifiants incorrects."

    return render_template("login.html", error=error)


@bp.route("/inscription", methods=["GET", "POST"])
def inscription():
    if request.method == "POST":
        db = get_db()
        hashed_password = generate_password_hash(request.form.get("password"))
        default_avatar = "default_avatar.png"
        default_banner = "default_banner.jpg"

        with db.cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (username, display_name, email, password_hash, avatar_url, banner_url)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                request.form.get("username"),
                request.form.get("display_name"),
                request.form.get("email"),
                hashed_password,
                default_avatar,
                default_banner
            ))
            db.commit()

        return redirect(url_for("main.connexion"))

    return render_template("inscription.html")


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.connexion"))


# -------------------------------------------------
# Notifications
# -------------------------------------------------

@bp.route("/notifications")
@login_required
def notifications():
    db = get_db()
    current_user_id = session["user_id"]

    with db.cursor() as cursor:
        cursor.execute("""
            SELECT
                n.id,
                n.user_id,
                n.sender_id,
                n.post_id,
                n.reply_id,
                n.message_id,
                n.type,
                n.is_read,
                n.created_at,

                u.username AS sender_username,
                u.display_name AS sender_display_name,
                u.avatar_url AS sender_avatar_url,

                p.content AS post_content,
                p.media_url AS post_media_url,

                r.content AS reply_content,

                m.content AS message_content
            FROM notifications n
            JOIN users u ON u.id = n.sender_id
            LEFT JOIN posts p ON p.id = n.post_id
            LEFT JOIN posts r ON r.id = n.reply_id
            LEFT JOIN messages m ON m.id = n.message_id
            WHERE n.user_id = %s
            ORDER BY n.created_at DESC
        """, (current_user_id,))
        notifications = cursor.fetchall()

        cursor.execute("""
            UPDATE notifications
            SET is_read = 1
            WHERE user_id = %s
              AND is_read = 0
        """, (current_user_id,))
        db.commit()

    return render_template("notif.html", notifications=notifications)


# -------------------------------------------------
# Messages privés
# -------------------------------------------------

@bp.route("/messages")
@login_required
def messages_page():
    db = get_db()
    current_user_id = session["user_id"]
    selected_user_id = request.args.get("user_id", type=int)

    with db.cursor() as cursor:
        cursor.execute("""
            SELECT 
                u.id AS other_user_id,
                u.username,
                u.display_name,
                u.avatar_url,
                m.content AS last_message,
                m.created_at AS last_message_date,
                (
                    SELECT COUNT(*)
                    FROM messages unread
                    WHERE unread.sender_id = u.id
                      AND unread.receiver_id = %s
                      AND unread.is_read = 0
                ) AS unread_count
            FROM messages m
            JOIN users u
                ON u.id = CASE
                    WHEN m.sender_id = %s THEN m.receiver_id
                    ELSE m.sender_id
                END
            JOIN (
                SELECT
                    CASE
                        WHEN sender_id = %s THEN receiver_id
                        ELSE sender_id
                    END AS other_user_id,
                    MAX(created_at) AS max_date
                FROM messages
                WHERE sender_id = %s OR receiver_id = %s
                GROUP BY other_user_id
            ) latest
                ON latest.other_user_id = u.id
               AND latest.max_date = m.created_at
            WHERE (m.sender_id = %s OR m.receiver_id = %s)
            ORDER BY m.created_at DESC
        """, (
            current_user_id,
            current_user_id,
            current_user_id,
            current_user_id, current_user_id,
            current_user_id, current_user_id
        ))
        conversations = cursor.fetchall()

        selected_user = None
        if selected_user_id and selected_user_id != current_user_id:
            cursor.execute("""
                SELECT id, username, display_name, avatar_url
                FROM users
                WHERE id = %s
            """, (selected_user_id,))
            selected_user = cursor.fetchone()

    return render_template(
        "messages.html",
        conversations=conversations,
        selected_user=selected_user
    )


@bp.route("/api/users/search")
@login_required
def search_users():
    db = get_db()
    current_user_id = session["user_id"]
    query = request.args.get("q", "").strip()

    if not query:
        return {"users": []}

    with db.cursor() as cursor:
        cursor.execute("""
            SELECT u.id, u.username, u.display_name, u.avatar_url
            FROM users u
            JOIN follows f ON f.following_id = u.id
            WHERE f.follower_id = %s
              AND u.id != %s
              AND (u.username LIKE %s OR u.display_name LIKE %s)
            ORDER BY u.display_name ASC
            LIMIT 10
        """, (
            current_user_id,
            current_user_id,
            f"%{query}%",
            f"%{query}%"
        ))
        users = cursor.fetchall()

    return {"users": users}


@bp.route("/api/messages/conversations")
@login_required
def get_conversations():
    db = get_db()
    current_user_id = session["user_id"]

    with db.cursor() as cursor:
        cursor.execute("""
            SELECT 
                u.id AS other_user_id,
                u.username,
                u.display_name,
                u.avatar_url,
                m.content AS last_message,
                m.created_at AS last_message_date,
                (
                    SELECT COUNT(*)
                    FROM messages unread
                    WHERE unread.sender_id = u.id
                      AND unread.receiver_id = %s
                      AND unread.is_read = 0
                ) AS unread_count
            FROM messages m
            JOIN users u
                ON u.id = CASE
                    WHEN m.sender_id = %s THEN m.receiver_id
                    ELSE m.sender_id
                END
            JOIN (
                SELECT
                    CASE
                        WHEN sender_id = %s THEN receiver_id
                        ELSE sender_id
                    END AS other_user_id,
                    MAX(created_at) AS max_date
                FROM messages
                WHERE sender_id = %s OR receiver_id = %s
                GROUP BY other_user_id
            ) latest
                ON latest.other_user_id = u.id
               AND latest.max_date = m.created_at
            WHERE (m.sender_id = %s OR m.receiver_id = %s)
            ORDER BY m.created_at DESC
        """, (
            current_user_id,
            current_user_id,
            current_user_id,
            current_user_id, current_user_id,
            current_user_id, current_user_id
        ))
        conversations = cursor.fetchall()

    return {"conversations": conversations}


@bp.route("/api/messages/<int:user_id>")
@login_required
def get_messages(user_id):
    db = get_db()
    current_user_id = session["user_id"]

    if user_id == current_user_id:
        return {"messages": []}

    with db.cursor() as cursor:
        cursor.execute("""
            SELECT 1
            FROM follows
            WHERE follower_id = %s
              AND following_id = %s
            LIMIT 1
        """, (current_user_id, user_id))
        allowed = cursor.fetchone()

        if not allowed:
            return {"error": "Accès refusé."}, 403

        cursor.execute("""
            SELECT *
            FROM messages
            WHERE (sender_id = %s AND receiver_id = %s)
               OR (sender_id = %s AND receiver_id = %s)
            ORDER BY created_at ASC
        """, (current_user_id, user_id, user_id, current_user_id))
        messages = cursor.fetchall()

    return {"messages": messages}


@bp.route("/api/messages/send/<int:user_id>", methods=["POST"])
@login_required
def send_message(user_id):
    db = get_db()
    current_user_id = session["user_id"]

    if user_id == current_user_id:
        return {"error": "Tu ne peux pas t'envoyer un message à toi-même."}, 400

    data = request.get_json(silent=True) or {}
    content = (data.get("content") or "").strip()

    if not content:
        return {"error": "Message vide."}, 400

    with db.cursor() as cursor:
        cursor.execute("""
            SELECT id
            FROM users
            WHERE id = %s
        """, (user_id,))
        target_user = cursor.fetchone()

        if not target_user:
            return {"error": "Utilisateur introuvable."}, 404

        cursor.execute("""
            SELECT 1
            FROM follows
            WHERE follower_id = %s
              AND following_id = %s
            LIMIT 1
        """, (current_user_id, user_id))
        allowed = cursor.fetchone()

        if not allowed:
            return {"error": "Tu peux seulement envoyer un message à un compte que tu suis."}, 403

        cursor.execute("""
            INSERT INTO messages (sender_id, receiver_id, content)
            VALUES (%s, %s, %s)
        """, (current_user_id, user_id, content))

        message_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO notifications (user_id, sender_id, post_id, reply_id, message_id, type, is_read)
            VALUES (%s, %s, NULL, NULL, %s, 'message', 0)
        """, (user_id, current_user_id, message_id))

        db.commit()

    return {"success": True}


@bp.route("/api/messages/read/<int:user_id>", methods=["POST"])
@login_required
def mark_as_read(user_id):
    db = get_db()
    current_user_id = session["user_id"]

    with db.cursor() as cursor:
        cursor.execute("""
            UPDATE messages
            SET is_read = 1
            WHERE sender_id = %s
              AND receiver_id = %s
              AND is_read = 0
        """, (user_id, current_user_id))
        db.commit()

    return {"success": True}