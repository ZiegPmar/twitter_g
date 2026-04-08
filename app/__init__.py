from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman
import os # Ajouté pour la bonne pratique des clés secrètes

def create_app():
    app = Flask(__name__)

    # 1. CLÉ SECRÈTE
    # On utilise une valeur par défaut pour le Lab, mais prêt pour os.environ
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'h4ufhuzehphduhs144fhuehôùsgdfpieh44vsdph5')

    # 2. ACTIVATION DE LA PROTECTION CSRF (Faille 4.1)
    # Correction Ruff : On initialise directement sans assignation de variable inutilisée
    CSRFProtect(app)

    # 3. SÉCURISATION DES SESSIONS ET COOKIES (Faille 6.3)
    app.config.update(
        SESSION_COOKIE_SECURE=False,  # Mets à True si tu utilises HTTPS
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
    )

    # 4. EN-TÊTES DE SÉCURITÉ : CSP, CLICKJACKING, HSTS
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
            "https://api.open-meteo.com",
            "https://cdn.jsdelivr.net"
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
    Talisman(app, content_security_policy=csp, force_https=False)

    from . import routes
    app.register_blueprint(routes.bp)

    return app