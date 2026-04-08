import pymysql
from flask import g

def get_db():
    if 'db' not in g:
        g.db = pymysql.connect(
            # On sépare bien l'IP et le port !
            host='212.227.84.80', # Juste l'IP, sans les deux points
            port=3307,            # Le port ici, SANS guillemets (c'est un chiffre)
            
            user='root',     # Mets ton vrai user
            password= 'root_password', # Mets ton vrai mdp
            database= 'g_twitter',     # Mets ta vraie BDD
            
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_app(app):
    app.teardown_appcontext(close_db)