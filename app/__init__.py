from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman
import os
import hvac # Client OpenBao

def get_secrets():
    """Récupère dynamiquement la clé secrète depuis OpenBao"""
    bao_url = os.environ.get('BAO_ADDR', 'http://212.227.84.80:8200')
    role_id = os.environ.get('BAO_ROLE_ID')
    secret_id = os.environ.get('BAO_SECRET_ID')

    # Si on n'a pas les IDs (dev local), on garde une clé de secours
    if not role_id or not secret_id:
        return os.environ.get('SECRET_KEY', 'dev-key-unsafe-h4ufhuzeh')

    try:
        client = hvac.Client(url=bao_url)
        # Auth via AppRole
        client.auth.approle.login(role_id=role_id, secret_id=secret_id)
        
        # Lecture du secret
        read_response = client.secrets.kv.v2.read_secret_version(
            mount_point='secret', 
            path='twitter_guardia'
        )
        return read_response['data']['data']['flask_key']
    except Exception as e:
        print(f"❌ Erreur OpenBao : {e}")
        return "fallback-key-error-check-logs"

def create_app():
    app = Flask(__name__)

    # 1. CLÉ SECRÈTE (Récupérée dynamiquement via OpenBao)
    app.config['SECRET_KEY'] = get_secrets()

    # 2. ACTIVATION DE LA PROTECTION CSRF (Faille 4.1)
    CSRFProtect(app)

    # 3. SÉCURISATION DES SESSIONS ET COOKIES (Faille 6.3)
    # Note: Passe SESSION_COOKIE_SECURE à True car tu es en HTTPS avec Traefik
    app.config.update(
        SESSION_COOKIE_SECURE=True,  
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