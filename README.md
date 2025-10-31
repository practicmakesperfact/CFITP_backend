# CFITP – Backend

Django 5 + DRF backend for client feedback & issue tracking.

---

## Features
- Role-based access: `client`, `staff`, `manager`, `admin`  
- JWT auth (SimpleJWT)  
- Issue workflow + history  
- Threaded comments with @mentions → notifications  
- Feedback → Issue conversion  
- File attachments (local / S3-ready)  
- In-app + email notifications (Celery)  
- Async CSV/PDF reports  
- Swagger UI: `/api/docs/`  
- Full test suite + `seed.py`

---

## Folder Structure
![alt text](image.png)

---

## Local Setup (Pure Python)

```bash
git clone https://github.com/practicmakesperfact/CFITP_backend.git
cd CFITP_backend

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

##PostgreSQL
CREATE DATABASE cfitp_db;
CREATE USER cfitp_user WITH PASSWORD 'yourpass';
GRANT ALL PRIVILEGES ON DATABASE cfitp_db TO cfitp_user;

##Redis (Ubuntu)
bashsudo apt install redis-server -y
sudo service redis-server start

##.env
envSECRET_KEY=dev-key-change-in-prod
DEBUG=True
DB_NAME=cfitp_db
DB_USER=cfitp_user
DB_PASSWORD=yourpass
DB_HOST=localhost
DB_PORT=5432
REDIS_URL=redis://localhost:6379/1
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

##Run
```bash
python manage.py makemigrations
python manage.py migrate
python seed.py
python manage.py runserver

##Celery (new terminal)
```bash
celery -A cf_celery_config worker -l info

##Test
```bash
python manage.py test

##Seed Data
```bash
python seed.py

Final API Endpoints (All Working)







































































































































MethodURLPurposePOST/api/v1/auth/register/RegisterPOST/api/v1/auth/login/LoginPOST/api/v1/auth/logout/LogoutPOST/api/v1/auth/refresh/Refresh tokenGET/api/v1/users/me/ProfileGET/api/v1/issues/List issuesPOST/api/v1/issues/Create issueGET/api/v1/issues/{id}/DetailPATCH/api/v1/issues/{id}/UpdatePOST/api/v1/issues/{id}/assign/AssignPOST/api/v1/issues/{id}/transition/Change statusGET/api/v1/issues/{id}/comments/List commentsPOST/api/v1/issues/{id}/comments/Add commentPATCH/api/v1/comments/{id}/Edit commentDELETE/api/v1/comments/{id}/DeleteGET/api/v1/feedback/ListPOST/api/v1/feedback/SubmitPOST/api/v1/feedback/{id}/convert/ConvertPOST/api/v1/attachments/UploadGET/api/v1/attachments/{id}/download/DownloadGET/api/v1/notifications/ListPOST/api/v1/notifications/{id}/mark-read/Mark readPOST/api/v1/reports/Request reportGET/api/v1/reports/{id}/View report—/api/docs/Swagger UI