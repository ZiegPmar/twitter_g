# --- ÉTAPE 1 : BUILDER (Construction) ---
# On utilise une image complète pour installer les dépendances
FROM python:3.11-slim AS builder

WORKDIR /app

# Installation des dépendances dans un répertoire spécifique
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# --- ÉTAPE 2 : RUNTIME (Exécution) ---
# Utilisation de l'image Distroless (Bonus : pas de shell, pas de root)
FROM gcr.io/distroless/python3

WORKDIR /app

# Copie uniquement les dépendances installées (Challenge : réduction de surface)
COPY --from=builder /root/.local /root/.local
# Copie uniquement le code nécessaire (évite de copier .git, tests, etc.)
COPY app/ ./app/
COPY run.py .

# Configuration de l'environnement Python pour trouver les libs
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/root/.local/lib/python3.11/site-packages

# Force l'utilisation d'un utilisateur non-privilégié (Challenge : Non-root)
USER nonroot

# Port d'écoute de ton app Flask/FastAPI
EXPOSE 5000

# Commande de lancement (Distroless n'a pas besoin de "python" devant car c'est l'entrypoint)
CMD ["run.py"]