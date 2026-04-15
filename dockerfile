# --- ÉTAPE 1 : BUILDER (Construction) ---
FROM python:3.11-slim AS builder

# Définition du répertoire de travail
WORKDIR /app

# Copie du fichier de dépendances
COPY requirements.txt .

# Installation des dépendances dans un dossier spécifique (/app/package)
# Cela permet d'isoler les bibliothèques pour la copie vers l'image finale
RUN pip install --no-cache-dir --target=/app/package -r requirements.txt

# --- ÉTAPE 2 : RUNTIME (Exécution) ---
# Utilisation de Distroless Debian 12 (plus récent, compatible Python 3.11)
FROM gcr.io/distroless/python3-debian12

WORKDIR /app

# Copie des bibliothèques installées depuis l'étape builder
COPY --from=builder /app/package /app/package

# Copie du code source de l'application
COPY app/ ./app/
COPY run.py .

# --- CONFIGURATION ENVIRONNEMENT ---
# Variable CRUCIALE : on force Python à inclure le dossier des packages dans son chemin de recherche
ENV PYTHONPATH=/app/package

# Désactivation de la génération de fichiers .pyc (plus léger pour le conteneur)
ENV PYTHONDONTWRITEBYTECODE=1
# Force l'affichage des logs en temps réel dans Render
ENV PYTHONUNBUFFERED=1

# Utilisation de l'utilisateur non-privilégié inclus dans l'image Distroless
USER nonroot

# Port d'écoute (5000 par défaut pour Flask)
EXPOSE 5000

# Lancement de l'application
# Sur Distroless, l'entrypoint est déjà l'interpréteur python
CMD ["run.py"]