# MyCloudOS

MyCloudOS est un SaaS full-stack en Python (backend + frontend) pour simuler une plateforme de cloud computing multi-OS.

## Fonctionnalites

- Authentification: creation de compte, connexion, verification de compte par code + lien.
- Dashboard cloud: creation d'instances avec OS (Windows, Ubuntu, Debian, Fedora), choix region/CPU/RAM/disque.
- Provisioning asynchrone simule avec statut et IP publique generee.
- Boite de messages de dev pour verifier les emails localement.

## Stack technique

- Backend: FastAPI
- Frontend: Jinja2 + CSS custom
- Base de donnees: SQLite
- Auth: session cookie + hash bcrypt

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
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8009
```

5. Dans un second terminal, demarrer le frontend (port 3009):

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 3009
```

6. Ouvrir l'application:

- Frontend: http://127.0.0.1:3009
- Backend/API: http://127.0.0.1:8009
- Emails de verification (mode local): http://127.0.0.1:3009/dev/messages

Option scripts:

```powershell
.\run-backend.ps1
.\run-frontend.ps1
```

## Notes importantes

- Ce projet est un MVP: le provisioning est simule localement (pas de creation reelle de VM cloud).
- L'architecture est prevue pour brancher un provider cloud reel (Azure, OpenStack, VMware, etc.) dans `app/services/cloud_service.py`.
