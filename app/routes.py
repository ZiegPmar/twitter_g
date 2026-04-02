import os
from flask import Blueprint, render_template, request, redirect, url_for, current_app, session, abort
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from .db import get_db

bp = Blueprint("main", __name__)

# Configuration pour la sécurité des fichiers
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_CONTENT_LENGTH = 1000 # Limite de caractères pour les posts/bios

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route("/")
def feed():
    if 'user_id' not in session:
        return redirect(url_for("main.connexion"))
        
    db = get_db()
    current_user_id = session['user_id']

    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE id = %s", (current_user_id,))
        current_user = cursor.fetchone()

        cursor.execute("""
            SELECT
                posts.id, posts.user_id, posts.content, posts.media_url, posts.created_at,
                users.username, users.display_name, users.avatar_url,
                COUNT(DISTINCT likes.id) AS like_count,
                COUNT(DISTINCT replies.id) AS comment_count,
                EXISTS (
                    SELECT 1 FROM likes AS my_like
                    WHERE my_like.post_id = posts.id AND my_like.user_id = %s
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
                SELECT posts.id, posts.content, posts.created_at,
                       users.username, users.display_name, users.avatar_url
                FROM posts
                JOIN users ON users.id = posts.user_id
                WHERE posts.reply_to_post_id = %s
                ORDER BY posts.created_at DESC LIMIT 3
            """, (post["id"],))
            comments_preview = cursor.fetchall()
            post["comments_preview"] = [dict(comment) for comment in comments_preview]
            posts.append(post)

    return render_template("home.html", posts=posts, current_user=current_user)

#-------------------------------------------------------------
# Ajout d'un post (Sécurisé)
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

    # Validation de longueur (Prévention DoS)
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

        # Sécurisation de l'upload
        if media_file and media_file.filename != "" and allowed_file(media_file.filename):
            ext = media_file.filename.rsplit('.', 1)[-1].lower()
            # On ne fait jamais confiance au nom original : on en génère un nouveau
            new_filename = secure_filename(f"{username}_{post_id}_image.{ext}")
            
            upload_folder = os.path.join(current_app.root_path, "static", "img", "post")
            os.makedirs(upload_folder, exist_ok=True) 
            
            media_file.save(os.path.join(upload_folder, new_filename))
            media_url = url_for('static', filename=f'img/post/{new_filename}')

            cursor.execute("UPDATE posts SET media_url = %s WHERE id = %s", (media_url, post_id))

    db.commit() 
    return redirect(request.referrer or url_for("main.feed"))

#-------------------------------------------------------------
# Système de like/unlike (Requiert CSRF protection côté HTML)
#-------------------------------------------------------------

@bp.route("/like/<int:post_id>", methods=["POST"])
def like_post(post_id):
    if 'user_id' not in session:
        return redirect(url_for("main.connexion"))
        
    db = get_db()
    user_id = session['user_id']

    with db.cursor() as cursor:
        cursor.execute("SELECT id FROM likes WHERE user_id = %s AND post_id = %s", (user_id, post_id))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO likes (user_id, post_id) VALUES (%s, %s)", (user_id, post_id))
            db.commit()

    return redirect(request.referrer or url_for("main.feed"))

@bp.route("/unlike/<int:post_id>", methods=["POST"])
def unlike_post(post_id):
    if 'user_id' not in session:
        return redirect(url_for("main.connexion"))
        
    db = get_db()
    user_id = session['user_id']

    with db.cursor() as cursor:
        cursor.execute("DELETE FROM likes WHERE user_id = %s AND post_id = %s", (user_id, post_id))
        db.commit()

    return redirect(request.referrer or url_for("main.feed"))

@bp.route("/comment/<int:post_id>", methods=["POST"])
def add_comment(post_id):
    if 'user_id' not in session:
        return redirect(url_for("main.connexion"))
        
    content = request.form.get("content", "").strip()
    if not content or len(content) > MAX_CONTENT_LENGTH:
        return redirect(request.referrer or url_for("main.feed"))

    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("""
            INSERT INTO posts (user_id, content, media_url, reply_to_post_id)
            VALUES (%s, %s, %s, %s)
        """, (session['user_id'], content, None, post_id))
        db.commit()

    return redirect(request.referrer or url_for("main.feed"))

#----------------------------------
# Affichage et Suppression
#----------------------------------

@bp.route("/post/<int:post_id>")
def view_post(post_id):
    db = get_db()
    current_user_id = session.get('user_id') 

    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE id = %s", (current_user_id,))
        current_user = cursor.fetchone()

        cursor.execute("""
            SELECT
                posts.id, posts.user_id, posts.content, posts.media_url, posts.created_at,
                users.username, users.display_name, users.avatar_url,
                COUNT(DISTINCT likes.id) AS like_count,
                COUNT(DISTINCT replies.id) AS comment_count,
                EXISTS (
                    SELECT 1 FROM likes AS my_like
                    WHERE my_like.post_id = posts.id AND my_like.user_id = %s
                ) AS liked_by_me
            FROM posts
            JOIN users ON users.id = posts.user_id
            LEFT JOIN likes ON likes.post_id = posts.id
            LEFT JOIN posts AS replies ON replies.reply_to_post_id = posts.id
            WHERE posts.id = %s
            GROUP BY posts.id, posts.user_id, posts.content, posts.media_url, posts.created_at,
                     users.username, users.display_name, users.avatar_url
        """, (current_user_id, post_id))
        post = cursor.fetchone()

        if not post:
            abort(404)

        cursor.execute("""
            SELECT posts.id, posts.content, posts.created_at,
                   users.username, users.display_name, users.avatar_url
            FROM posts
            JOIN users ON users.id = posts.user_id
            WHERE posts.reply_to_post_id = %s
            ORDER BY posts.created_at ASC
        """, (post_id,))
        comments = cursor.fetchall()

    return render_template("view_post.html", post=post, comments=comments, current_user=current_user)

@bp.route("/delete-post/<int:post_id>", methods=["POST"])
def delete_post(post_id):
    if 'user_id' not in session:
        return redirect(url_for("main.connexion"))
        
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT user_id FROM posts WHERE id = %s", (post_id,))
        post = cursor.fetchone()

        # Vérification stricte de propriété (Broken Access Control)
        if post is None or post["user_id"] != session['user_id']:
            abort(403)

        cursor.execute("DELETE FROM posts WHERE id = %s", (post_id,))
        db.commit()

    return redirect(url_for("main.feed"))

#------------------------------
# Profil (Sécurisé)
#------------------------------

@bp.route("/profile/<username>")
def profile(username):
    if 'user_id' not in session:
        return redirect(url_for("main.connexion"))
        
    db = get_db()
    current_user_id = session['user_id']

    with db.cursor() as cursor:
        # 1. Infos du profil visité
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if user is None:
            abort(404)

        # 2. Est-ce que je suis ce profil ?
        cursor.execute("SELECT 1 FROM follows WHERE follower_id = %s AND following_id = %s", 
                       (current_user_id, user['id']))
        is_following = cursor.fetchone() is not None

        # --- NOUVEAU : COMPTEURS DYNAMIQUES ---
        # 3. Nombre d'abonnés (ceux qui suivent ce profil)
        cursor.execute("SELECT COUNT(*) as total FROM follows WHERE following_id = %s", (user['id'],))
        followers_count = cursor.fetchone()['total']

        # 4. Nombre d'abonnements (ceux que ce profil suit)
        cursor.execute("SELECT COUNT(*) as total FROM follows WHERE follower_id = %s", (user['id'],))
        following_count = cursor.fetchone()['total']
        # ---------------------------------------

        # 5. Récupération des posts
        cursor.execute("""
            SELECT posts.*, users.username, users.display_name, users.avatar_url,
            (SELECT COUNT(*) FROM likes WHERE post_id = posts.id) as like_count,
            (SELECT COUNT(*) FROM posts as p2 WHERE p2.reply_to_post_id = posts.id) as comment_count,
            EXISTS(SELECT 1 FROM likes WHERE user_id = %s AND post_id = posts.id) as liked_by_me
            FROM posts 
            JOIN users ON posts.user_id = users.id 
            WHERE posts.user_id = %s AND posts.reply_to_post_id IS NULL
            ORDER BY posts.created_at DESC
        """, (current_user_id, user['id']))
        
        raw_posts = cursor.fetchall()
        posts = []
        for row in raw_posts:
            post = dict(row)
            # (Ta logique de comments_preview ici...)
            posts.append(post)

    # Récupération de l'utilisateur connecté pour la sidebar
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE id = %s", (current_user_id,))
        logged_in_user = cursor.fetchone()

    # ON ENVOIE LES COMPTEURS AU TEMPLATE
    return render_template("profil.html", 
                       user=user, 
                       posts=posts, 
                       current_user=logged_in_user, 
                       is_following=is_following,
                       followers_count=followers_count, # <--- ICI
                       following_count=following_count) # <--- ICI

@bp.route("/edit-profile", methods=["GET", "POST"])
def edit_profile():
    if 'user_id' not in session:
        return redirect(url_for("main.connexion"))
    
    db = get_db()
    current_user_id = session['user_id']
    username = session['username']

    if request.method == "POST":
        display_name = request.form.get("display_name", "").strip()
        bio = request.form.get("bio", "").strip()
        email = request.form.get("email", "").strip()

        # Validation de base
        if len(bio) > MAX_CONTENT_LENGTH or len(display_name) > 100:
            return "Entrée trop longue", 400

        avatar_file = request.files.get("avatar")
        banner_file = request.files.get("banner")

        with db.cursor() as cursor:
            cursor.execute("""
                UPDATE users SET display_name = %s, bio = %s, email = %s
                WHERE id = %s
            """, (display_name, bio, email, current_user_id))
            
            # Traitement sécurisé Avatar
            if avatar_file and avatar_file.filename != "" and allowed_file(avatar_file.filename):
                ext = avatar_file.filename.rsplit('.', 1)[-1].lower()
                avatar_filename = secure_filename(f"{username}_avatar.{ext}")
                upload_folder = os.path.join(current_app.root_path, "static", "img", "Avatar")
                os.makedirs(upload_folder, exist_ok=True)
                avatar_file.save(os.path.join(upload_folder, avatar_filename))
                cursor.execute("UPDATE users SET avatar_url = %s WHERE id = %s", (avatar_filename, current_user_id))

            # Traitement sécurisé Bannière
            if banner_file and banner_file.filename != "" and allowed_file(banner_file.filename):
                ext = banner_file.filename.rsplit('.', 1)[-1].lower()
                banner_filename = secure_filename(f"{username}_banner.{ext}")
                upload_folder = os.path.join(current_app.root_path, "static", "img", "banniere")
                os.makedirs(upload_folder, exist_ok=True)
                banner_file.save(os.path.join(upload_folder, banner_filename))
                cursor.execute("UPDATE users SET banner_url = %s WHERE id = %s", (banner_filename, current_user_id))
            
            db.commit()
        return redirect(url_for("main.profile", username=username))

    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE id = %s", (current_user_id,))
        current_user = cursor.fetchone()

    return render_template("edit_profil.html", current_user=current_user)

#------------------------------
# Système de Follow
#------------------------------

@bp.route("/follow/<int:target_user_id>", methods=["POST"])
def follow_user(target_user_id):
    if 'user_id' not in session:
        return redirect(url_for("main.connexion"))
        
    current_user_id = session['user_id']
    if current_user_id == target_user_id:
        return "Impossible de se suivre soi-même", 400

    db = get_db()
    with db.cursor() as cursor:
        # On vérifie si le lien existe déjà
        cursor.execute("SELECT id FROM follows WHERE follower_id = %s AND following_id = %s", 
                       (current_user_id, target_user_id))
        follow_rel = cursor.fetchone()

        if follow_rel:
            # Si existe -> Unfollow
            cursor.execute("DELETE FROM follows WHERE follower_id = %s AND following_id = %s", 
                           (current_user_id, target_user_id))
        else:
            # Si n'existe pas -> Follow
            cursor.execute("INSERT INTO follows (follower_id, following_id) VALUES (%s, %s)", 
                           (current_user_id, target_user_id))
        
        db.commit()

    return redirect(request.referrer or url_for("main.profile", username=session['username']))

#------------------------------
# Connexion / Inscription (Hachage Actif)
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
        
        # Comparaison sécurisée du hachage
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('main.feed'))
        error = "Identifiants incorrects."
    return render_template('login.html', error=error)

@bp.route('/inscription', methods=['GET', 'POST'])
def inscription():
    if request.method == 'POST':
        db = get_db()
        # Hachage du mot de passe avant insertion
        hashed_password = generate_password_hash(request.form.get('password'))
        with db.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (username, display_name, email, password_hash) VALUES (%s, %s, %s, %s)",
                (request.form.get('username'), request.form.get('display_name'), 
                 request.form.get('email'), hashed_password)
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