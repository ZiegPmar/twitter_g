from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman

def create_app():
    app = Flask(__name__)

    # 1. CLÉ SECRÈTE (Indispensable pour CSRF et Sessions)
    # En production, utilise une variable d'environnement : os.environ.get('SECRET_KEY')
    app.config['SECRET_KEY'] = 'h4ufhuzehphduhs144fhuehôùsgdfpieh44vsdph5'

    # 2. ACTIVATION DE LA PROTECTION CSRF (Faille 4.1)
    csrf = CSRFProtect(app)

    # 3. SÉCURISATION DES SESSIONS ET COOKIES (Faille 6.3)
    app.config.update(
        SESSION_COOKIE_SECURE=False,  # Mets à True si tu utilises HTTPS
        SESSION_COOKIE_HTTPONLY=True, # Empêche le vol de session via JS (XSS)
        SESSION_COOKIE_SAMESITE='Lax', # Protection supplémentaire contre CSRF
    )

    # 4. EN-TÊTES DE SÉCURITÉ : CSP, CLICKJACKING, HSTS (Failles 4.2, 4.4, 6.3)
    # Flask-Talisman configure tout ça d'un coup
    csp = {
        'default-src': "'self'",
        'script-src': [
            "'self'",
            "'unsafe-inline'",
            "https://cdn.jsdelivr.net",
            "https://cdnjs.cloudflare.com"
        ],
        'style-src': [
            "'self'",
            "'unsafe-inline'",
            "https://cdnjs.cloudflare.com",
            "https://cdn.jsdelivr.net",
            "https://fonts.googleapis.com"
        ],
        'connect-src': [
            "'self'",
            "https://api.open-meteo.com", # <--- LE LIEN DE TON FETCH
            "https://cdn.jsdelivr.net"     # Pour les données des Emojis
        ],
        'font-src': [
            "'self'",
            "https://cdnjs.cloudflare.com",
            "https://fonts.gstatic.com"
        ],
        'img-src': [
            "'self'", 
            "data:", 
            "https://openweathermap.org"
        ]
    }
    Talisman(app, content_security_policy=csp, force_https=False) # force_https=True en prod

    from . import routes
    app.register_blueprint(routes.bp)

    return app