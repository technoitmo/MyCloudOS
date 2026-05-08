# MyCloudOS

MyCloudOS est un SaaS full-stack en Python (backend + frontend) pour simuler une plateforme de cloud computing multi-OS.

## Fonctionnalites

- Authentification: creation de compte, connexion, verification de compte par code + lien.
- Dashboard cloud: creation d'instances avec OS (Windows, Ubuntu, Debian, Fedora), choix region/CPU/RAM/disque.
- Provisioning asynchrone simule avec statut et IP publique generee.
- Boite de messages de dev pour verifier les emails localement.
- Envoi email SMTP reel disponible via configuration.
- Provider cloud extensible: local (defaut) et OpenStack (optionnel).

## Stack technique

- Backend: FastAPI
- Frontend: Jinja2 + CSS custom
- Base de donnees: SQLite
- Auth: session cookie + hash bcrypt

## Structure du projet

- `backend/`: code Python FastAPI, logique metier, auth, services cloud.
- `frontend/`: application frontend autonome (pages + assets UI) qui consomme l'API backend.

## Lancer en local (Windows)

1. Creer et activer un environnement virtuel:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Installer les dependances:

```powershell
pip install -r requirements.txt
```

3. Configurer l'environnement:

```powershell
Copy-Item .env.example .env
```

4. Demarrer le backend (port 8009):

```powershell
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8009
```

5. Dans un second terminal, demarrer le frontend (port 3009):

```powershell
cd frontend
python -m uvicorn main:app --reload --host 127.0.0.1 --port 3009
```

6. Ouvrir l'application:

- Frontend: http://127.0.0.1:3009
- Backend/API: http://127.0.0.1:8009/api
- Emails de verification (mode local): http://127.0.0.1:8009/api/dev/messages

Option scripts:

```powershell
.\run-backend.ps1
.\run-frontend.ps1
```

## Notes importantes

- Ce projet est un MVP: le provisioning est simule localement (pas de creation reelle de VM cloud).
- L'architecture est prevue pour brancher un provider cloud reel (Azure, OpenStack, VMware, etc.) dans `backend/app/services/cloud_service.py`.

## Configuration Email

- `EMAIL_MODE=dev`: emails stockes localement et visibles dans `/dev/messages`.
- `EMAIL_MODE=smtp`: envoi reel via SMTP.

## API principales (backend)

- `POST /api/auth/register`
- `POST /api/auth/verify-code`
- `GET /api/auth/verify?token=...`
- `POST /api/auth/login`
- `GET /api/cloud/os-images`
- `GET /api/cloud/instances` (Bearer token requis)
- `POST /api/cloud/instances` (Bearer token requis)
- `GET /api/dev/messages` (uniquement si `EMAIL_MODE=dev`)

Variables SMTP principales:

- `EMAIL_FROM`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_USE_TLS`
- `SMTP_USE_SSL`

## Configuration Cloud Provider

- `CLOUD_PROVIDER=local`: provisioning simule (par defaut).
- `CLOUD_PROVIDER=openstack`: provisioning via OpenStack.

Pour OpenStack, installez le SDK:

```powershell
pip install openstacksdk
```

Puis configurez:

- `OPENSTACK_AUTH_URL`
- `OPENSTACK_USERNAME`
- `OPENSTACK_PASSWORD`
- `OPENSTACK_PROJECT_NAME`
- `OPENSTACK_USER_DOMAIN_NAME`
- `OPENSTACK_PROJECT_DOMAIN_NAME`
