from app import create_app
import os

app = create_app()

if __name__ == "__main__":
    # On récupère le mode debug via l'environnement
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"

    # Le "# nosec B104" dit à Bandit d'ignorer l'alerte sur l'adresse 0.0.0.0
    app.run(debug=debug_mode, host='0.0.0.0', port=8000)  


    buuuuuggg