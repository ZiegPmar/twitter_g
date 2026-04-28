# Projet développement de solution web sécurité

## Index
Votre nouveau réseau social préféré : G

G est un réseau social open source inspiré de Twitter/X, développé avec Flask et SQLite.
L'application permet aux utilisateurs de publier des posts, interagir avec leur communauté.

Projet réalisé dans le cadre d'un développement de solution web sécurité.

## Installation

```bash
git clone https://github.com/ton-user/twitter_g.git
cd twitter_g
```

```bash
pip install -r requirements.txt
```

## Fonctionnalités

### Accès & Authentification
- Inscription obligatoire pour accéder au site
- Connexion requise pour toutes les pages

### Accueil & Posts

* Publier des posts
* Consulter le fil d'actualité
* Liker, commenter et partager un post (vers d'autres applications)

### Profil

* Définir une photo de profil et une bannière
* Rédiger une biographie
* Consulter tous ses posts
* Voir son nombre d'abonnements et d'abonnés
* Afficher la date d'inscription

### Messages

* Envoyer et recevoir des messages privés

### Amis & Réseau

* Voir ses abonnements et ses abonnés

### Sidebar

* Widgets dynamiques
* Accès rapide à sa liste d'amis, ses messages et ses notifications

## Fonctionnalités cyber

**Contre les attaques actives**
- Protection **CSRF** — jetons anti-CSRF sur tous les formulaires (Flask-WTF)
- Protection **XSS** — auto-échappement natif via le moteur de template Jinja2
- Protection **SQLi** — requêtes SQL paramétrées, aucune injection possible
- Protection **Clickjacking** — en-tête `X-Frame-Options: DENY` ou `SAMEORIGIN`

**Configuration serveur**
- **Content Security Policy (CSP)** — restriction des scripts aux domaines de confiance
- **CORS** — politique inter-domaines restreinte, pas de wildcard `*`
- **SRI** — attribut `integrity` avec hash SHA-384/512 sur les scripts externes
- **HSTS** — `Strict-Transport-Security` activé (Flask-Talisman)
- **SameSite cookies** — protection contre les requêtes inter-domaines

**Authentification**
- Mots de passe avec exigences de complexité (longueur, majuscules, chiffres, symboles)
- Limitation des tentatives de connexion (anti-brute force)
- Hachage + salage des mots de passe

**Scan**
- **Gitleaks** : détecte les secrets et tokens accidentellement exposés dans le code
- **Flake8** : vérifie la qualité et la conformité du code Python
- **Bandit** : analyse le code source à la recherche de vulnérabilités Python
- **pip-audit** : contrôle les dépendances et détecte les paquets vulnérables
- **Trivy** : scanne l'image Docker à la recherche de CVE connues
- **OWASP ZAP** : teste l'application en conditions réelles pour détecter les failles web


## Patch notes

### Nosec B104

**Analyse de l'alerte :**

L'instruction host='0.0.0.0' indique au serveur de liaison de s'attacher à toutes les interfaces réseau disponibles. Dans un environnement de production strict, cela peut exposer l'application à des accès non désirés si le réseau n'est pas correctement segmenté.

**Contexte d'utilisation :**

Dans notre cas, ce choix est délibéré afin de faciliter le déploiement rapide et la conteneurisation (Docker). Le tag # nosec permet de maintenir un pipeline CI/CD "propre" sans bloquer sur des alertes connues et acceptées dans ce périmètre de développement. En environnement de production critique, cette pratique est proscrite. 

## Deploiement

### GHCR 

#### **Fonctionnement sur la pipeline**

***Préparation de l'environnement*** 

- Checkout 
- Login a ghcr.io en utilisant un token temporaire (GITHUB_TOKEN)

***Gestion des tags***

```yaml
- name: Extract metadata (tags, labels)
  id: meta
  uses: docker/metadata-action@v5
  with:
    images: ghcr.io/${{ github.repository }}
    tags: |
      type=raw,value=latest      
      type=raw,value=dev         
      type=sha,prefix=sha-       
```

***Build et Push***

```yaml
- name: Build et push Docker image
  uses: docker/build-push-action@v5
  with:
    context: .                
    push: true                
    tags: ${{ steps.meta.outputs.tags }}     
    labels: ${{ steps.meta.outputs.labels }} 
```

#### **Récupérer et utiliser l'image**

***S'authentifier***

```bash
docker login ghcr.io
```

***Choisir la version souhaiter***

- Pour la version la plus stable :

```bash
docker pull ghcr.io/<username>/<repo-name>:latest
```

- Pour une version liée à un commit :

```bash
docker pull ghcr.io/<username>/<repo-name>:sha-<commit_id>
```

***Lancer le conteneur***

```bash
docker run -p 8080:8080 ghcr.io/<username>/<repo-name>:latest
```

##### **Consulter les images sur GitHub**

--> Rendez-vous sur la page principale du dépôt.

--> Regardez dans la colonne de droite, section Packages.

--> Cliquez sur l'image pour voir l'historique complet des tags (SHA, dev, latest).

### Render

#### **Healthcheck et Monitoring**

##### **Endpoint /health**

&nbsp;

***Création de la route***

```python
@app.route('/health')
def health_check():
    return "OK", 200
```

***Vérification avec curl***

```bash
curl -I http://localhost:8080/health
```

##### **Uptime Kuma**

#### **Config dans l'interface**

- Type de moniteur : HTTP(s)

- URL : http://<ton-ip-ou-domaine>:8080/health

- Intervalle de test : 60 secondes (par défaut)

**Système d'alerte**

- Seuil d'alerte : Si l'endpoint /health ne répond pas avec un code 200 pendant 3 tests consécutifs, le service est considéré comme DOWN.

- Notifications : Kuma est configuré pour envoyer une alerte immédiate (via un webhook Discord)

### Rollback

#### **Rollback Manuel**

```bash
# Remplacer 'sha-buggy' par le 'sha-stable' précédent trouvé sur GHCR
docker pull ghcr.io/<pseudo>/<repo>:sha-a1b2c3d
docker run -d ghcr.io/<pseudo>/<repo>:sha-a1b2c3d
```

#### **Rollback automatique**

***Modif dans la route***

```python
APP_IS_BROKEN = False # Seulement en face de test du rollback

@app.route('/health')
def health():
    # Si le bug est activé, on renvoie une erreur 500
    if APP_IS_BROKEN:
        return {
            "status": "DOWN",
            "reason": "Critical feature failed"
        }, 500  
    
    # Sinon, tout va bien
    return {
        "status": "UP",
        "uptime": "100%",
        "version": "sha-v2"
    }, 200
```

***Modif dans la pipeline***

```yaml
- name: Vérification et Rollback automatique
  run: |
    echo "Démarrage des tests de santé..."
    
    sleep 10 
    
    STATUS_CODE=$(curl -o /dev/null -s -w "%{http_code}" http://localhost:8080/health)
    
    if [ "$STATUS_CODE" -ne 200 ]; then
      echo "❌ Erreur $STATUS_CODE détectée sur la nouvelle version !"
      echo "Démarrage du ROLLBACK AUTOMATIQUE..."

      docker stop mon_app_container || true
      docker run -d --name mon_app_container ghcr.io/${{ github.repository }}:latest
      
      echo "✅ Rollback terminé. L'ancienne version stable est en ligne."
      exit 1 # On fait échouer le job pour prévenir l'utilisateur
    else
      echo "✅ Healthcheck réussi (200 OK). Déploiement validé."
    fi
```

### Scalabilité

#### **Avec Docker Compose**

```bash
docker-compose up --scale app=2 -d
```

#### **Ajout de Nginx**

```yaml
services:
  app:
    image: ghcr.io/mon-pseudo/mon-app:latest
    deploy:
      replicas: 2 # Optionnel, peut être fait via la commande --scale

  nginx:
    image: nginx:latest
    ports:
      - "80:80"
    depends_on:
      - app
```

Après l'ajout du Nginx on peut vérifier si la scalabilité fonctionne avec les logs

```bash
docker-compose logs -f
```

### Stratégie de déploiement

#### **Blue/Green Deployment**

***Dans le docker-compose.yml***

```yaml
services:
  app-blue: # Version actuelle (Stable)
    image: ghcr.io/mon-repo:v1
  app-green: # Nouvelle version (Target)
    image: ghcr.io/mon-repo:v2
```

***Dans le nginx.conf***

```bash
# Modifier le point d'entrée vers app-green dans la config nginx
sed -i 's/app-blue/app-green/g' ./nginx/default.conf

docker exec nginx-proxy nginx -s reload
```

#### **Rolling Update**

```yaml
deploy:
  update_config:
    parallelism: 1         # On en met à jour 1 à la fois
    delay: 10s             # On attend 10s entre chaque
    failure_action: rollback 
```

#### **Canary**

***Architecture du projet***

Pour que cela fonctionne, nous faisons tourner deux services simultanément dans le docker-compose.yml derrière un proxy Nginx :

- Service **app-stable** : La version actuelle.

- Service **app-canary** : La nouvelle version à tester.

***Configuration de Nginx***

```bash
upstream my_app {
    # 90% des utilisateurs vont ici
    server app-stable:8080 weight=9; 
    
    # 10% des utilisateurs testent la nouveauté
    server app-canary:8080 weight=1; 
}

server {
    listen 80;
    location / {
        proxy_pass http://my_app;
    }
}
```

***Mettre en deploiement Canary***

Pour activer le Canary, on déploie la nouvelle version sans couper l'ancienne :

```bash
# 1. Lancer la version Canary
docker-compose up -d app-canary

# 2. Appliquer la nouvelle configuration Nginx
docker exec nginx-proxy nginx -s reload

# 3. Surveiller les logs du Canary spécifiquement
docker logs -f app-canary
```

### Gestion des Secrets

#### **OpenBao**

***État et Initialisation***

```bash
# Vérifier l'état (scellé ou non, initialisé ou non)
bao status

# Initialiser le coffre (génère les clés d'unseal et le Root Token)
# À ne faire qu'une seule fois !
bao operator init

# Déverrouiller le coffre (nécessite généralement 3 clés sur 5)
bao operator unseal <clé_1>
bao operator unseal <clé_2>
bao operator unseal <clé_3>
```

***Authentification***

```bash
# Se connecter avec le Root Token (pour l'admin)
bao login <votre_root_token>
```

***Gestion des Secrets***

```bash
# Activer le moteur de secrets (si pas déjà fait)
bao secrets enable -path=secret kv-v2

# Créer ou mettre à jour un secret
bao kv put secret/my-app-secrets db_password="mon_password_incroyable" api_key="XYZ123"

# Lire un secret pour vérifier
bao kv get secret/my-app-secrets

# Lister tous les chemins de secrets disponibles
bao kv list secret/
```
***Gestion des Droits***

```bash
# Créer une politique à partir d'un fichier hcl
bao policy write my-app-policy ./policy.hcl

# Générer un Token limité pour l'application (utilisé dans ton routes.py)
bao token create -policy="my-app-policy"
```

***Modification dans route.py***
```python
import hvac

def get_secret_from_bao(path, key):
    # Connexion à l'instance OpenBao
    client = hvac.Client(url='http://openbao:8200', token=os.getenv('BAO_TOKEN'))
    
    # Lecture du secret
    read_response = client.secrets.kv.v2.read_secret_version(path=path)
    return read_response['data']['data'][key]

@app.route('/health')
def health():
    # On vérifie dynamiquement si on peut toujours joindre le coffre-fort
    try:
        db_password = get_secret_from_bao('my-app-secrets', 'db_password')
        return {"status": "UP", "vault": "connected"}, 200
    except Exception as e:
        return {"status": "DEGRADED", "reason": "Vault unreachable"}, 500

```

***Mettre a jour un secret manuellement***

```bash
bao kv put secret/my-app-secrets db_password="nouveau_mdp_ultra_secure"
```
