from flask import Blueprint, render_template, request, redirect, url_for
from .db import get_db

bp = Blueprint("main", __name__)

@bp.route("/")
def feed():
    db = get_db()
    current_user_id = 1

    raw_posts = db.execute("""
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
                  AND my_like.user_id = ?
            ) AS liked_by_me
        FROM posts
        JOIN users ON users.id = posts.user_id
        LEFT JOIN likes ON likes.post_id = posts.id
        LEFT JOIN posts AS replies ON replies.reply_to_post_id = posts.id
        WHERE posts.reply_to_post_id IS NULL
        GROUP BY posts.id, posts.user_id, posts.content, posts.media_url, posts.created_at,
                 users.username, users.display_name, users.avatar_url
        ORDER BY posts.created_at DESC
    """, (current_user_id,)).fetchall()

    posts = []

    for row in raw_posts:
        post = dict(row)

        comments_preview = db.execute("""
            SELECT
                posts.id,
                posts.content,
                posts.created_at,
                users.username,
                users.display_name,
                users.avatar_url
            FROM posts
            JOIN users ON users.id = posts.user_id
            WHERE posts.reply_to_post_id = ?
            ORDER BY posts.created_at DESC
            LIMIT 3
        """, (post["id"],)).fetchall()

        post["comments_preview"] = [dict(comment) for comment in comments_preview]
        posts.append(post)

    return render_template("home.html", posts=posts)

#-------------------------------------------------------------
# Ajout d'un post ( temporaire dans l'état )
#-------------------------------------------------------------

@bp.route("/add-post", methods=["POST"])
def add_post():
    db = get_db()

    content = request.form.get("content", "").strip()
    media_url = request.form.get("media_url", "").strip()

    if not content:
        return redirect(url_for("main.feed"))

    user_id = 1

    db.execute("""
        INSERT INTO posts (user_id, content, media_url)
        VALUES (?, ?, ?)
    """, (user_id, content, media_url if media_url else None))

    db.commit()

    return redirect(url_for("main.feed"))

#-------------------------------------------------------------
# Système de like/unlike basique, à améliorer avec le login
#-------------------------------------------------------------

@bp.route("/like/<int:post_id>", methods=["POST"])
def like_post(post_id):
    db = get_db()
    user_id = 1 # A supprimer quand login sera ok

    existing_like = db.execute("""
        SELECT id FROM likes
        WHERE user_id = ? AND post_id = ?
    """, (user_id, post_id)).fetchone()

    if existing_like is None:
        db.execute("""
            INSERT INTO likes (user_id, post_id)
            VALUES (?, ?)
        """, (user_id, post_id))
        db.commit()

    return redirect(url_for("main.feed"))

@bp.route("/unlike/<int:post_id>", methods=["POST"])
def unlike_post(post_id):
    db = get_db()
    user_id = 1  # temporaire

    db.execute("""
        DELETE FROM likes
        WHERE user_id = ? AND post_id = ?
    """, (user_id, post_id))
    db.commit()

    return redirect(url_for("main.feed"))

#----------------------------------
# Système de commentaires basique
#----------------------------------

@bp.route("/comment/<int:post_id>", methods=["POST"])
def add_comment(post_id):
    db = get_db()
    user_id = 1  # temporaire

    content = request.form.get("content", "").strip()

    if not content:
        return redirect(url_for("main.feed"))

    db.execute("""
        INSERT INTO posts (user_id, content, media_url, reply_to_post_id)
        VALUES (?, ?, ?, ?)
    """, (user_id, content, None, post_id))

    db.commit()

    return redirect(url_for("main.feed"))

@bp.route("/post/<int:post_id>")
def view_post(post_id):
    db = get_db()

    post = db.execute("""
        SELECT
            posts.id,
            posts.content,
            posts.media_url,
            posts.created_at,
            users.username,
            users.display_name,
            users.avatar_url
        FROM posts
        JOIN users ON users.id = posts.user_id
        WHERE posts.id = ?
    """, (post_id,)).fetchone()

    comments = db.execute("""
        SELECT
            posts.id,
            posts.content,
            posts.created_at,
            users.username,
            users.display_name,
            users.avatar_url
        FROM posts
        JOIN users ON users.id = posts.user_id
        WHERE posts.reply_to_post_id = ?
        ORDER BY posts.created_at ASC
    """, (post_id,)).fetchall()

    return render_template("post.html", post=post, comments=comments)

#----------------
# Delete un post
#----------------

@bp.route("/delete-post/<int:post_id>", methods=["POST"])
def delete_post(post_id):
    db = get_db()
    current_user_id = 1  # temporaire

    post = db.execute("""
        SELECT id, user_id
        FROM posts
        WHERE id = ?
    """, (post_id,)).fetchone()

    if post is None:
        return redirect(url_for("main.feed"))

    if post["user_id"] != current_user_id:
        return redirect(url_for("main.feed"))

    db.execute("""
        DELETE FROM likes
        WHERE post_id = ?
    """, (post_id,))

    db.execute("""
        DELETE FROM posts
        WHERE reply_to_post_id = ?
    """, (post_id,))

    db.execute("""
        DELETE FROM posts
        WHERE id = ?
    """, (post_id,))

    db.commit()

    return redirect(url_for("main.feed"))