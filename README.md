A complete Django 5 + DRF backend for a client-feedback / internal-issue tracker.
Fully tested, seed-ready, and frontend-ready (React + Tailwind will be a separate repo).

Features

FeatureStatusRole-based users (client, staff, manager, admin)DoneJWT auth (SimpleJWT) with refresh/revokeDoneIssue workflow + historyDoneThreaded comments with @mention → notificationDoneFeedback → Issue conversionDoneFile attachments (local dev / S3 prod)DoneIn-app + email notifications (Celery)DoneAsync CSV/PDF reportsDoneSwagger UI (/api/docs/)DoneFull test suite + seed.pyDone

Folder Structure (exact)
textCFITP/
├── __pycache__/
├── apps/
│   ├── attachments/
│   ├── comments/
│   ├── feedback/
│   ├── issues/
│   ├── notifications/
│   ├── reports/
│   └── users/
├── CFIT/
│   ├── media/               # uploaded files (dev)
│   └── venv/                # (optional) local virtualenv
├── .env
├── .gitignore
├── cf_celery_config.py
├── manage.py
├── requirements.txt
├── seed.py                  # demo data
└── tasks.py                 # Celery tasks

Local Development (Pure Python – no Docker)
1. Clone & cd
bashgit clone https://github.com/<you>/cfitp-backend.git
cd cfitp-backend
2. Virtualenv
bashpython -m venv .venv
source .venv/bin/activate      # Linux/macOS
# .venv\Scripts\activate       # Windows
3. Install
bashpip install -r requirements.txt
4. PostgreSQL
sqlsudo -u postgres psql
CREATE DATABASE cfitp_db;
CREATE USER cfitp_user WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE cfitp_db TO cfitp_user;
\q
5. Redis (Ubuntu)
bashsudo apt install redis-server -y
sudo service redis-server start
redis-cli ping   # → PONG
6. .env (root)
envSECRET_KEY=super-secret-dev-key
DEBUG=True

DB_NAME=cfitp_db
DB_USER=cfitp_user
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432

REDIS_URL=redis://localhost:6379/1

EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
7. Migrate & Seed
bashpython manage.py makemigrations
python manage.py migrate
python seed.py
8. Run Server
bashpython manage.py runserver
9. Run Celery (new terminal)
bashcelery -A CFIT worker -l info

URLs

































URLPurposehttp://127.0.0.1:8000/api/docs/Swagger UIhttp://127.0.0.1:8000/admin/Django AdminPOST /api/v1/auth/login/Get JWTGET /api/v1/issues/List issuesPOST /api/v1/issues/{id}/comments/Add commentPOST /api/v1/feedback/Submit feedback

Default password for all seeded users: password123


Testing
bashpytest
# or
python manage.py test

Seed Data (seed.py)
bashpython seed.py