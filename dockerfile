# --- ÉTAPE 1 : BUILDER (Construction) ---
# On utilise une image slim pour compiler/installer les dépendances
FROM python:3.11-slim AS builder

# Empêcher Python de générer des fichiers .pyc et forcer l'affichage des logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Installation des outils nécessaires pour certaines libs (si besoin)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copie du fichier de dépendances
COPY requirements.txt .

# On installe les dépendances dans /install au lieu de /root/.local
# Cela permet d'éviter les problèmes de permissions avec l'utilisateur nonroot
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# --- ÉTAPE 2 : RUNTIME (Exécution) ---
# Utilisation de l'image Distroless pour une sécurité maximale
FROM gcr.io/distroless/python3-debian12

WORKDIR /app

# Copie des bibliothèques installées depuis l'étape builder vers /usr/local
# C'est le chemin standard que Python consulte par défaut
COPY --from=builder /install /usr/local

# Copie du code source et du point d'entrée
COPY app/ ./app/
COPY run.py .

# Configuration cruciale de l'environnement :
# 1. On pointe vers le dossier exact des site-packages de Python 3.11
# 2. On s'assure que les binaires installés sont dans le PATH
ENV PYTHONPATH=/usr/local/lib/python3.11/site-packages
ENV PATH=/usr/local/bin:$PATH

# Force l'utilisation d'un utilisateur sans privilèges (sécurité Distroless)
USER nonroot

# Port d'écoute (Render utilise souvent 10000 par défaut, Flask utilise 5000)
# Assure-toi que ton run.py écoute sur 0.0.0.0
EXPOSE 5000

# Commande de lancement
# Note : Distroless python3 a déjà l'entrypoint configuré sur l'exécutable python
CMD ["run.py"]