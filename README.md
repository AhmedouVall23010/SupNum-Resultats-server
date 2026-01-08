# SupNum Résultats - Authentication API

API d'authentification sécurisée avec JWT pour la plateforme SupNum Résultats.

## 📋 Prérequis

- Python 3.10 ou supérieur
- MongoDB (local ou distant)
- pip (gestionnaire de paquets Python)

## 🚀 Installation et Configuration

### 1. Cloner le projet (si nécessaire)

```bash
cd /home/ahmedou/SupNum/S5/python/projet/server
```

### 2. Créer un environnement virtuel (Virtual Environment)

```bash
python3 -m venv venv
```

ou

```bash
python -m venv venv
```

### 3. Activer l'environnement virtuel

#### Sur Linux/Mac:
```bash
source venv/bin/activate
```

#### Sur Windows:
```bash
venv\Scripts\activate
```

**Note**: Après activation, vous verrez `(venv)` au début de votre ligne de commande.

### 4. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 5. Configuration de l'environnement

Créez un fichier `.env` à la racine du projet (optionnel, les valeurs par défaut sont dans `app/core/config.py`):

```env
# MongoDB Configuration
MONGODB_URL=mongodb://admin:123456@localhost:27017
DATABASE_NAME=app_db

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=noreply@supnum.mr
FRONTEND_URL=http://localhost:3000
FRONTEND_VITE_URL=http://localhost:5173

# Cookie Configuration
REFRESH_TOKEN_COOKIE_NAME=refresh_token
REFRESH_TOKEN_COOKIE_HTTP_ONLY=True
REFRESH_TOKEN_COOKIE_SECURE=False
REFRESH_TOKEN_COOKIE_SAME_SITE=lax
```

## ▶️ Lancer le serveur

### Mode développement (avec rechargement automatique)

```bash
uvicorn app.main:app --reload
```

### Mode production

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Le serveur sera accessible à:
- **API**: http://localhost:8000
- **Documentation Swagger**: http://localhost:8000/docs
- **Documentation ReDoc**: http://localhost:8000/redoc


