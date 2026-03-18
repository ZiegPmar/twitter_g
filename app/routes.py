from flask import Blueprint, render_template, request, redirect, url_for, current_app
from .db import get_db
import os

bp = Blueprint("main", __name__)

@bp.route("/")
def feed():
    db = get_db()
    current_user_id = 1

    with db.cursor() as cursor:
        cursor.execute("""
            SELECT *
            FROM users
            WHERE id = %s
        """, (current_user_id,))
        current_user = cursor.fetchone()

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
            GROUP BY posts.id, posts.user_id, posts.content, posts.media_url, posts.created_at,
                     users.username, users.display_name, users.avatar_url
            ORDER BY posts.created_at DESC
        """, (current_user_id,))
        raw_posts = cursor.fetchall()

        posts = []

        for row in raw_posts:
            post = dict(row)

            cursor.execute("""
                SELECT
                    posts.id,
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

            post["comments_preview"] = [dict(comment) for comment in comments_preview]
            posts.append(post)

    return render_template("home.html", posts=posts, current_user=current_user)

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

    with db.cursor() as cursor:
        cursor.execute("""
            INSERT INTO posts (user_id, content, media_url)
            VALUES (%s, %s, %s)
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

    with db.cursor() as cursor:
        cursor.execute("""
            SELECT id FROM likes
            WHERE user_id = %s AND post_id = %s
        """, (user_id, post_id))
        existing_like = cursor.fetchone()

        if existing_like is None:
            cursor.execute("""
                INSERT INTO likes (user_id, post_id)
                VALUES (%s, %s)
            """, (user_id, post_id))
            db.commit()

    # Redirige là d'où vient l'utilisateur (feed, profil ou view_post)
    return redirect(request.referrer or url_for("main.feed"))

@bp.route("/unlike/<int:post_id>", methods=["POST"])
def unlike_post(post_id):
    db = get_db()
    user_id = 1  # temporaire

    with db.cursor() as cursor:
        cursor.execute("""
            DELETE FROM likes
            WHERE user_id = %s AND post_id = %s
        """, (user_id, post_id))
        db.commit()

    # Redirige là d'où vient l'utilisateur
    return redirect(request.referrer or url_for("main.feed"))

#----------------------------------
# Système de commentaires basique
#----------------------------------

@bp.route("/comment/<int:post_id>", methods=["POST"])
def add_comment(post_id):
    db = get_db()
    user_id = 1  # temporaire

    content = request.form.get("content", "").strip()

    if not content:
        return redirect(request.referrer or url_for("main.feed"))

    with db.cursor() as cursor:
        cursor.execute("""
            INSERT INTO posts (user_id, content, media_url, reply_to_post_id)
            VALUES (%s, %s, %s, %s)
        """, (user_id, content, None, post_id))
        db.commit()

    # Redirige là d'où vient l'utilisateur (feed ou view_post)
    return redirect(request.referrer or url_for("main.feed"))

#----------------------------------
# Afficher un post en grand
#----------------------------------

@bp.route("/post/<int:post_id>")
def view_post(post_id):
    db = get_db()
    current_user_id = 1  # temporaire

    with db.cursor() as cursor:
        # 1. On récupère les infos de l'utilisateur connecté (pour la sidebar)
        cursor.execute("SELECT * FROM users WHERE id = %s", (current_user_id,))
        current_user = cursor.fetchone()

        # 2. On récupère le post visé, AVEC le compte de likes et commentaires
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
                posts.id, posts.user_id, posts.content, posts.media_url, posts.created_at,
                users.username, users.display_name, users.avatar_url
        """, (current_user_id, post_id))
        post = cursor.fetchone()

        if not post:
            return redirect(url_for("main.feed")) # Si le post n'existe pas, retour à l'accueil

        # 3. On récupère TOUS les commentaires de ce post
        cursor.execute("""
            SELECT
                posts.id,
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
        comments = cursor.fetchall()

    return render_template("view_post.html", post=post, comments=comments, current_user=current_user)

#----------------
# Delete un post
#----------------

@bp.route("/delete-post/<int:post_id>", methods=["POST"])
def delete_post(post_id):
    db = get_db()
    current_user_id = 1  # temporaire

    with db.cursor() as cursor:
        cursor.execute("""
            SELECT id, user_id
            FROM posts
            WHERE id = %s
        """, (post_id,))
        post = cursor.fetchone()

        if post is None:
            return redirect(url_for("main.feed"))

        if post["user_id"] != current_user_id:
            return redirect(url_for("main.feed"))

        cursor.execute("""
            DELETE FROM posts
            WHERE id = %s
        """, (post_id,))
        db.commit()

    return redirect(url_for("main.feed"))

#------------------------------
# Redirige vers les profiles
#------------------------------

@bp.route("/profile/<username>")
def profile(username):
    db = get_db()
    current_user_id = 1

    with db.cursor() as cursor:
        cursor.execute("""
            SELECT *
            FROM users
            WHERE username = %s
        """, (username,))
        user = cursor.fetchone()

        if user is None:
            return "Utilisateur introuvable", 404

        cursor.execute("""
            SELECT
                posts.id,
                posts.content,
                posts.media_url,
                posts.created_at
            FROM posts
            WHERE user_id = %s
              AND reply_to_post_id IS NULL
            ORDER BY created_at DESC
        """, (user["id"],))
        posts = cursor.fetchall()

    return render_template("profil.html", user=user, posts=posts)


@bp.route("/login")
def login():
    return render_template("login.html")


@bp.route("/monprofil")
def monprofil():
    db = get_db()
    current_user_id = 1 # À remplacer plus tard 

    with db.cursor() as cursor:
        cursor.execute("""
            SELECT *
            FROM users
            WHERE id = %s
        """, (current_user_id,))
        current_user = cursor.fetchone()

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
                users.banner_url,  -- Ajouté pour être sûr de l'avoir
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
              AND posts.user_id = %s -- IMPORTANT : On ne veut que TES posts sur ton profil
            GROUP BY 
                posts.id, posts.user_id, posts.content, posts.media_url, posts.created_at,
                users.username, users.display_name, users.avatar_url, users.banner_url
            ORDER BY posts.created_at DESC
        """, (current_user_id, current_user_id))
        raw_posts = cursor.fetchall()

        posts = []

        for row in raw_posts:
            post = dict(row)

            cursor.execute("""
                SELECT
                    posts.id,
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

            post["comments_preview"] = [dict(comment) for comment in comments_preview]
            posts.append(post)

    return render_template("profil.html", posts=posts, current_user=current_user)

@bp.route("/update-profile", methods=["POST"])
def update_profile():
    db = get_db()
    current_user_id = 1
    
    with db.cursor() as cursor:
        cursor.execute("SELECT username, avatar_url, banner_url FROM users WHERE id = %s", (current_user_id,))
        user = cursor.fetchone()
    
    username = user['username'].replace(" ", "_") # On remplace les espaces par des underscores
    
    # --- CHEMINS ABSOLUS ---
    # current_app.root_path pointe vers le dossier racine de ton application
    avatar_dir = os.path.join(current_app.root_path, 'static', 'img', 'Avatar')
    banner_dir = os.path.join(current_app.root_path, 'static', 'img', 'banniere')

    # Création automatique des dossiers s'ils n'existent pas
    os.makedirs(avatar_dir, exist_ok=True)
    os.makedirs(banner_dir, exist_ok=True)

    # --- GESTION AVATAR ---
    avatar_file = request.files.get("avatar")
    new_avatar_name = user['avatar_url']
    if avatar_file and avatar_file.filename != '':
        ext = os.path.splitext(avatar_file.filename)[1]
        new_avatar_name = f"{username}_avatar{ext}"
        avatar_file.save(os.path.join(avatar_dir, new_avatar_name))

    # --- GESTION BANNIÈRE ---
    banner_file = request.files.get("banner")
    new_banner_name = user['banner_url']
    if banner_file and banner_file.filename != '':
        ext = os.path.splitext(banner_file.filename)[1]
        new_banner_name = f"{username}_banniere{ext}"
        banner_file.save(os.path.join(banner_dir, new_banner_name))

    # --- MISE À JOUR BDD ---
    with db.cursor() as cursor:
        cursor.execute("""
            UPDATE users 
            SET display_name = %s, bio = %s, email = %s, avatar_url = %s, banner_url = %s 
            WHERE id = %s
        """, (request.form.get("display_name"), 
              request.form.get("bio"), 
              request.form.get("email"), 
              new_avatar_name, 
              new_banner_name, 
              current_user_id))
        db.commit()
        
    return redirect(url_for('main.monprofil'))

@bp.route("/edit-profile")
def edit_profile():
    db = get_db()
    current_user_id = 1 # Temporaire, comme le reste de ton code

    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE id = %s", (current_user_id,))
        current_user = cursor.fetchone()

    return render_template("edit_profil.html", current_user=current_user)


@bp.route("/test")
def test():
    return "ok"