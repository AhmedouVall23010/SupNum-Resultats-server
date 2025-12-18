# 📚 Documentation API - SupNum Résultats Authentication

## 🔐 Flow Complet d'Authentification

### Vue d'ensemble
- **Base URL**: `http://localhost:8000` (ou votre URL de production)
- **Content-Type**: `application/json`
- **Authentication**: Bearer Token dans header `Authorization`

---

## 📋 Endpoints Disponibles

### 1. **POST /auth/register** - Inscription

**Description**: Créer un nouveau compte utilisateur

**Request Body**:
```json
{
  "email": "ahmedou@supnum.mr",
  "password": "password123"
}
```

**Validation**:
- `email`: Doit se terminer par `@supnum.mr`
- `password`: Minimum 6 caractères

**Response Success (201)**:
```json
{
  "message": "Registration successful. Please check your email to verify your account.",
  "email": "ahmedou@supnum.mr"
}
```

**Response Error (400)**:
```json
{
  "detail": "Email already registered and verified. Please login instead."
}
```

**Flow**:
1. Utilisateur envoie email + password
2. Backend crée le compte avec `role = "student"` et `email_verified = false`
3. Backend envoie email de vérification
4. Utilisateur doit vérifier son email avant de pouvoir se connecter

---

### 2. **GET /auth/verify-email** - Vérification Email

**Description**: Vérifier l'email avec le token reçu par email

**Query Parameters**:
- `token` (string, required): Token reçu dans l'email

**Request Example**:
```
GET /auth/verify-email?token=1VejCHIAQFHxILYSFYjNWQzMnPHkEvDhO9JWruRjRk
```

**Response Success (200)**:
```json
{
  "message": "Email verified successfully. You can now login."
}
```

**Response Error (400)**:
```json
{
  "detail": "Invalid or expired verification token"
}
```

**Flow**:
1. Utilisateur clique sur le lien dans l'email
2. Frontend redirige vers `/verify-email?token=...`
3. Frontend appelle `GET /auth/verify-email?token=...`
4. Si succès → rediriger vers page de login

**Note**: Token valide pendant 24 heures, usage unique

---

### 3. **POST /auth/login** - Connexion

**Description**: Se connecter et obtenir les tokens

**Request Body**:
```json
{
  "email": "ahmedou@supnum.mr",
  "password": "password123"
}
```

**Response Success (200)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "email": "ahmedou@supnum.mr",
    "role": "student",
    "email_verified": true,
    "is_active": true,
    "created_at": "2024-01-01T10:00:00",
    "updated_at": "2024-01-01T10:00:00"
  }
}
```

**⚠️ IMPORTANT - Refresh Token**:
- Le `refresh_token` est envoyé dans un **Cookie HttpOnly Secure**
- **NE PAS** essayer de le lire depuis JavaScript
- Il est automatiquement envoyé avec chaque requête
- Nom du cookie: `refresh_token`

**Response Error (401)**:
```json
{
  "detail": "Incorrect email or password"
}
```

**Response Error (403)**:
```json
{
  "detail": "Please verify your email before logging in. Check your inbox for the verification link."
}
```

**Flow**:
1. Utilisateur envoie email + password
2. Backend vérifie les credentials
3. Backend vérifie que `email_verified = true`
4. Backend crée `access_token` (30 minutes) et `refresh_token` (7 jours)
5. `access_token` dans response body → **stocker en RAM seulement**
6. `refresh_token` dans cookie → **géré automatiquement par le navigateur**

**⚠️ Stockage Access Token**:
- ✅ **Stocker en RAM** (state, context, store)
- ❌ **NE PAS** stocker dans localStorage
- ❌ **NE PAS** stocker dans sessionStorage
- ❌ **NE PAS** stocker dans cookie

---

### 4. **POST /auth/refresh** - Rafraîchir Access Token

**Description**: Obtenir un nouvel access token quand l'ancien expire

**Request Body**: 
**AUCUN** - Le refresh token est lu automatiquement depuis le cookie

**Request Headers**: Aucun header spécial requis

**Response Success (200)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Response Error (401)**:
```json
{
  "detail": "Invalid refresh token"
}
```

**Flow**:
1. Access token expire → API retourne 401
2. Frontend appelle automatiquement `POST /auth/refresh`
3. Backend lit `refresh_token` depuis cookie automatiquement
4. Backend vérifie et crée nouvel `access_token`
5. Frontend met à jour `access_token` en RAM
6. Frontend réessaie la requête originale

**Exemple d'implémentation**:
```javascript
// Intercepteur axios/fetch
if (response.status === 401) {
  const newToken = await refreshAccessToken();
  // Réessayer la requête originale avec nouveau token
}
```

---

### 5. **POST /auth/logout** - Déconnexion

**Description**: Se déconnecter et révoquer le refresh token

**Request Body**: 
**AUCUN** - Le refresh token est lu automatiquement depuis le cookie

**Response Success (200)**:
```json
{
  "message": "Logged out successfully"
}
```

**Flow**:
1. Frontend appelle `POST /auth/logout`
2. Backend révoque le refresh token dans la DB
3. Backend supprime le cookie `refresh_token`
4. Frontend supprime `access_token` de la RAM
5. Rediriger vers page de login

---

### 6. **POST /auth/forgot-password** - Demande de Réinitialisation

**Description**: Demander un lien de réinitialisation de mot de passe

**Request Body**:
```json
{
  "email": "ahmedou@supnum.mr"
}
```

**Response Success (200)**:
```json
{
  "message": "Si un compte existe avec cet email et qu'il est activé, un lien de réinitialisation a été envoyé."
}
```

**⚠️ IMPORTANT - Sécurité**:
- **Toujours** retourne le même message, même si le compte n'existe pas
- Cela empêche l'énumération d'emails
- L'email n'est envoyé que si:
  - Le compte existe
  - Le compte est actif (`is_active = true`)
  - L'email est vérifié (`email_verified = true`)

**Flow**:
1. Utilisateur entre son email
2. Frontend envoie `POST /auth/forgot-password`
3. Backend retourne toujours le même message
4. Si conditions remplies → email envoyé avec lien (valide 1 heure)

---

### 7. **POST /auth/reset-password** - Réinitialiser Mot de Passe

**Description**: Réinitialiser le mot de passe avec le token reçu par email

**Request Body**:
```json
{
  "token": "1VejCHIAQFHxILYSFYjNWQzMnPHkEvDhO9JWruRjRk",
  "new_password": "newpassword123"
}
```

**Validation**:
- `token`: Token reçu dans l'email
- `new_password`: Minimum 6 caractères

**Response Success (200)**:
```json
{
  "message": "Password reset successfully. Please login with your new password."
}
```

**Response Error (400)**:
```json
{
  "detail": "Invalid or expired reset token"
}
```

**Flow**:
1. Utilisateur clique sur lien dans email
2. Frontend affiche formulaire de nouveau mot de passe
3. Utilisateur entre nouveau mot de passe
4. Frontend envoie `POST /auth/reset-password` avec token + new_password
5. Backend change le mot de passe
6. Backend révoque tous les refresh tokens (sécurité)
7. Rediriger vers page de login

**Note**: Token valide pendant 1 heure

---

### 8. **GET /auth/me** - Obtenir Utilisateur Actuel

**Description**: Obtenir les informations de l'utilisateur connecté

**Request Headers**:
```
Authorization: Bearer <access_token>
```

**Response Success (200)**:
```json
{
  "id": "507f1f77bcf86cd799439011",
  "email": "ahmedou@supnum.mr",
  "role": "student",
  "email_verified": true,
  "is_active": true,
  "created_at": "2024-01-01T10:00:00",
  "updated_at": "2024-01-01T10:00:00"
}
```

**Response Error (401)**:
```json
{
  "detail": "Invalid authentication credentials"
}
```

**Flow**:
1. Frontend envoie requête avec `Authorization: Bearer <access_token>`
2. Backend décode le token et lit `name` et `role` depuis le token
3. Backend vérifie que le compte est toujours actif
4. Retourne les informations utilisateur

---

## 🔄 Flow Complet d'Authentification

### Scénario 1: Nouvel Utilisateur

```
1. POST /auth/register
   → { email, password }
   ← { message, email }

2. Utilisateur reçoit email → clique sur lien
   → GET /auth/verify-email?token=...
   ← { message: "Email verified..." }

3. POST /auth/login
   → { email, password }
   ← { access_token, token_type, user }
   + Cookie: refresh_token (HttpOnly)

4. Stocker access_token en RAM
5. Utiliser access_token pour requêtes API
```

### Scénario 2: Utilisateur Existant

```
1. POST /auth/login
   → { email, password }
   ← { access_token, token_type, user }
   + Cookie: refresh_token

2. Stocker access_token en RAM
3. Utiliser access_token pour requêtes API
```

### Scénario 3: Access Token Expiré

```
1. Requête API avec access_token expiré
   ← 401 Unauthorized

2. POST /auth/refresh (automatique)
   → (pas de body, cookie envoyé automatiquement)
   ← { access_token, token_type }

3. Mettre à jour access_token en RAM
4. Réessayer la requête originale
```

### Scénario 4: Mot de Passe Oublié

```
1. POST /auth/forgot-password
   → { email }
   ← { message: "Si un compte existe..." }

2. Utilisateur reçoit email → clique sur lien
3. Frontend affiche formulaire nouveau mot de passe

4. POST /auth/reset-password
   → { token, new_password }
   ← { message: "Password reset successfully..." }

5. Rediriger vers login
```

---

## 📦 Structure Access Token

Le `access_token` est un JWT qui contient:

```json
{
  "sub": "507f1f77bcf86cd799439011",  // User ID
  "name": "ahmedou",                  // Nom (partie avant @supnum.mr)
  "role": "student",                  // Role utilisateur
  "exp": 1234567890,                  // Expiration timestamp
  "iat": 1234567890                   // Issued at timestamp
}
```

**Durée de vie**: 30 minutes

**Utilisation**:
- Lire `name` et `role` directement depuis le token (pas besoin de requête DB)
- Utiliser pour vérifier les permissions

---

## 🛡️ Gestion des Erreurs

### Codes d'Erreur Communs

| Code | Signification | Action Frontend |
|------|---------------|-----------------|
| 401 | Token invalide/expiré | Appeler `/auth/refresh` ou rediriger vers login |
| 403 | Accès refusé (role/permissions) | Afficher message d'erreur |
| 400 | Données invalides | Afficher erreurs de validation |
| 404 | Ressource non trouvée | Afficher message d'erreur |

### Gestion 401 - Token Expiré

```javascript
// Exemple avec Axios
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      try {
        // Essayer de rafraîchir le token
        const { data } = await axios.post('/auth/refresh');
        // Mettre à jour access_token en RAM
        updateAccessToken(data.access_token);
        // Réessayer la requête originale
        return axios.request(error.config);
      } catch (refreshError) {
        // Refresh échoué → rediriger vers login
        redirectToLogin();
      }
    }
    return Promise.reject(error);
  }
);
```

---

## 🔐 Bonnes Pratiques Frontend

### 1. Stockage Access Token
```javascript
// ✅ CORRECT - En RAM
const [accessToken, setAccessToken] = useState(null); // React
// ou
const accessToken = ref(null); // Vue
// ou
store.state.auth.accessToken // Vuex/Redux

// ❌ INCORRECT
localStorage.setItem('access_token', token);
sessionStorage.setItem('access_token', token);
```

### 2. Envoi Access Token
```javascript
// ✅ CORRECT
fetch('/api/endpoint', {
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  }
});
```

### 3. Gestion Refresh Token
```javascript
// ✅ CORRECT - Le cookie est envoyé automatiquement
fetch('/auth/refresh', {
  method: 'POST',
  credentials: 'include' // Important pour envoyer les cookies
});
```

### 4. CORS Configuration
Assurez-vous que votre frontend envoie les credentials:
```javascript
fetch('/api/endpoint', {
  credentials: 'include' // Pour envoyer les cookies
});
```

---

## 📝 Exemples de Code Frontend

### React Example

```javascript
// Auth Context
const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [accessToken, setAccessToken] = useState(null);
  const [user, setUser] = useState(null);

  const login = async (email, password) => {
    const response = await fetch('http://localhost:8000/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include', // Important pour cookies
      body: JSON.stringify({ email, password })
    });
    
    const data = await response.json();
    setAccessToken(data.access_token); // En RAM
    setUser(data.user);
  };

  const refreshToken = async () => {
    const response = await fetch('http://localhost:8000/auth/refresh', {
      method: 'POST',
      credentials: 'include' // Cookie envoyé automatiquement
    });
    
    const data = await response.json();
    setAccessToken(data.access_token);
    return data.access_token;
  };

  const logout = async () => {
    await fetch('http://localhost:8000/auth/logout', {
      method: 'POST',
      credentials: 'include'
    });
    setAccessToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ accessToken, user, login, logout, refreshToken }}>
      {children}
    </AuthContext.Provider>
  );
};
```

### Axios Interceptor Example

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  withCredentials: true // Pour envoyer les cookies
});

// Ajouter access_token à chaque requête
api.interceptors.request.use((config) => {
  const token = getAccessTokenFromRAM(); // Votre fonction
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Gérer 401 - Token expiré
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      try {
        const { data } = await axios.post(
          'http://localhost:8000/auth/refresh',
          {},
          { withCredentials: true }
        );
        updateAccessTokenInRAM(data.access_token);
        // Réessayer la requête originale
        return api.request(error.config);
      } catch {
        // Rediriger vers login
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);
```

---

## 🎯 Checklist Frontend

- [ ] Stocker `access_token` en RAM uniquement
- [ ] Ne jamais stocker `access_token` dans localStorage/sessionStorage
- [ ] Ne jamais essayer de lire `refresh_token` (il est dans cookie HttpOnly)
- [ ] Configurer `credentials: 'include'` pour toutes les requêtes
- [ ] Implémenter interceptor pour gérer 401 automatiquement
- [ ] Appeler `/auth/refresh` quand access_token expire
- [ ] Supprimer `access_token` de RAM lors du logout
- [ ] Gérer les erreurs 401, 403, 400 correctement
- [ ] Afficher messages d'erreur appropriés à l'utilisateur

---

## 📞 Support

Pour toute question, contactez l'équipe backend.

**Base URL**: `http://localhost:8000`  
**Documentation API**: `http://localhost:8000/docs` (Swagger UI)

