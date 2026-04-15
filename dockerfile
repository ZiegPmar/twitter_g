# --- ÉTAPE 1 : BUILDER ---
FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt .
# On installe dans /install au lieu de /root/.local pour éviter les soucis de droits
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

# --- ÉTAPE 2 : RUNTIME ---
FROM gcr.io/distroless/python3-debian12:debug # Le tag debug aide si tu dois inspecter

WORKDIR /app

# On copie les libs depuis /install vers un dossier accessible
COPY --from=builder /install /usr/local

# Copie du code
COPY app/ ./app/
COPY run.py .

# Configuration pour que Python trouve les modules dans /usr/local
ENV PYTHONPATH=/usr/local/lib/python3.11/site-packages

# Utilisateur sécurisé
USER nonroot

# Port par défaut Render (souvent 10000, mais 5000 fonctionne si configuré)
EXPOSE 5000

# Sur Distroless Python, l'entrypoint est déjà 'python', on passe juste le fichier
CMD ["run.py"]