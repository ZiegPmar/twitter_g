# --- ÉTAPE 1 : BUILDER ---
FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt .
# On installe directement dans un dossier local pour être sûr du chemin
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- ÉTAPE 2 : RUNTIME (Distroless) ---
FROM gcr.io/distroless/python3-debian12 

WORKDIR /app

# Copie les libs depuis le dossier /install du builder
COPY --from=builder /install /usr/local

# Copie ton code
COPY app/ ./app/
COPY run.py .

# Pas besoin de modifier PYTHONPATH si on copie dans /usr/local
# car c'est le chemin par défaut de Python

USER nonroot
EXPOSE 5000

# Sur Distroless, l'entrypoint est déjà python, on passe juste le fichier
CMD ["run.py"]