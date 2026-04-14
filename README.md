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
