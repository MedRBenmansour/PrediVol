# Image de base légère, MÊME version de Python que l'entraînement (Colab : 3.13)
FROM python:3.13-slim

# Pas de fichiers .pyc, logs affichés tout de suite
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MLFLOW_DISABLE_AGENT_HINT=1

# Répertoire de travail dans le conteneur
WORKDIR /app

# 1. Les dépendances d'abord (Docker les garde en cache si requirements.txt ne change pas)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Le code de l'API et le modèle sérialisé
COPY app/ app/
COPY models/ models/

# 3. Sécurité : l'API ne tourne pas en administrateur (root)
RUN useradd --create-home api && chown -R api /app
USER api

# 4. Port de l'API et vérification automatique de son état (/health)
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"

# 5. Commande lancée au démarrage du conteneur
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]