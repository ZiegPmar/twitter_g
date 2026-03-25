import os
from flask import Blueprint, render_template, request, redirect, url_for, current_app, session
from .db import get_db

bp = Blueprint("main", __name__)

@bp.route("/")
def feed():
    if 'user_id' not in session:
        return redirect(url_for("main.connexion"))
        
    db = get_db()
    current_user_id = session['user_id']

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
# Ajout d'un post 
#-------------------------------------------------------------

@bp.route("/add-post", methods=["POST"])
def add_post():
    if 'user_id' not in session:
        return redirect(url_for("main.connexion"))
        
    db = get_db()
    user_id = session['user_id']
    username = session['username']

    content = request.form.get("content", "").strip()
    media_file = request.files.get("media")

    if not content and not media_file:
        return redirect(request.referrer or url_for("main.feed"))

    with db.cursor() as cursor:
        cursor.execute("""
            INSERT INTO posts (user_id, content, media_url)
            VALUES (%s, %s, NULL)
        """, (user_id, content))
        
        post_id = cursor.lastrowid

        if media_file and media_file.filename != "":
            ext = media_file.filename.rsplit('.', 1)[-1].lower()
            new_filename = f"{username}_{post_id}_image.{ext}"
            upload_folder = os.path.join("app", "static", "img", "post")
            os.makedirs(upload_folder, exist_ok=True) 
            
            filepath = os.path.join(upload_folder, new_filename)
            media_file.save(filepath)
            
            media_url = url_for('static', filename=f'img/post/{new_filename}')

            cursor.execute("""
                UPDATE posts 
                SET media_url = %s 
                WHERE id = %s
            """, (media_url, post_id))

    db.commit() 

    return redirect(request.referrer or url_for("main.feed"))

#-------------------------------------------------------------
# Système de like/unlike basique
#-------------------------------------------------------------

@bp.route("/like/<int:post_id>", methods=["POST"])
def like_post(post_id):
    if 'user_id' not in session:
        return redirect(url_for("main.connexion"))
        
    db = get_db()
    user_id = session['user_id']

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

    return redirect(request.referrer or url_for("main.feed"))

@bp.route("/unlike/<int:post_id>", methods=["POST"])
def unlike_post(post_id):
    if 'user_id' not in session:
        return redirect(url_for("main.connexion"))
        
    db = get_db()
    user_id = session['user_id']

    with db.cursor() as cursor:
        cursor.execute("""
            DELETE FROM likes
            WHERE user_id = %s AND post_id = %s
        """, (user_id, post_id))
        db.commit()

    return redirect(request.referrer or url_for("main.feed"))

#----------------------------------
# Système de commentaires basique
#----------------------------------

@bp.route("/comment/<int:post_id>", methods=["POST"])
def add_comment(post_id):
    if 'user_id' not in session:
        return redirect(url_for("main.connexion"))
        
    db = get_db()
    user_id = session['user_id']

    content = request.form.get("content", "").strip()

    if not content:
        return redirect(request.referrer or url_for("main.feed"))

    with db.cursor() as cursor:
        cursor.execute("""
            INSERT INTO posts (user_id, content, media_url, reply_to_post_id)
            VALUES (%s, %s, %s, %s)
        """, (user_id, content, None, post_id))
        db.commit()

    return redirect(request.referrer or url_for("main.feed"))

#----------------------------------
# Afficher un post en grand
#----------------------------------

@bp.route("/post/<int:post_id>")
def view_post(post_id):
    db = get_db()
    current_user_id = session.get('user_id', 1) 

    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE id = %s", (current_user_id,))
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
            WHERE posts.id = %s
            GROUP BY 
                posts.id, posts.user_id, posts.content, posts.media_url, posts.created_at,
                users.username, users.display_name, users.avatar_url
        """, (current_user_id, post_id))
        post = cursor.fetchone()

        if not post:
            return redirect(url_for("main.feed"))

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
    if 'user_id' not in session:
        return redirect(url_for("main.connexion"))
        
    db = get_db()
    current_user_id = session['user_id']

    with db.cursor() as cursor:
        cursor.execute("""
            SELECT id, user_id
            FROM posts
            WHERE id = %s
        """, (post_id,))
        post = cursor.fetchone()

        if post is None or post["user_id"] != current_user_id:
            return redirect(url_for("main.feed"))

        cursor.execute("""
            DELETE FROM posts
            WHERE id = %s
        """, (post_id,))
        db.commit()

    return redirect(url_for("main.feed"))

#------------------------------
# Profil unique
#------------------------------

@bp.route("/profile/<username>")
def profile(username):
    db = get_db()
    current_user_id = session.get('user_id')

    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
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
        
        cursor.execute("SELECT * FROM users WHERE id = %s", (current_user_id,))
        current_user = cursor.fetchone()

    return render_template("profil.html", user=user, posts=posts, current_user=current_user)

@bp.route("/edit-profile")
def edit_profile():
    db = get_db()
    current_user_id = 1 # Temporaire, comme le reste de ton code

    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE id = %s", (current_user_id,))
        current_user = cursor.fetchone()

    return render_template("edit_profil.html", current_user=current_user)


#------------------------------
# Connexion / Inscription
#------------------------------

@bp.route('/connexion', methods=['GET', 'POST'])
def connexion():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
        if user and user['password_hash'] == password:
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('main.feed'))
        error = "Identifiants incorrects."
    return render_template('login.html', error=error)

@bp.route('/inscription', methods=['GET', 'POST'])
def inscription():
    if request.method == 'POST':
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (username, display_name, email, password_hash) VALUES (%s, %s, %s, %s)",
                (request.form.get('username'), request.form.get('display_name'), 
                 request.form.get('email'), request.form.get('password'))
            )
            db.commit()
        return redirect(url_for('main.connexion'))
    return render_template('inscription.html')

@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.connexion"))

@bp.route("/test")
def test():
    return "ok"