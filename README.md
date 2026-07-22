# BloodMatch Backend

A Django REST Framework backend that connects blood donors with hospitals in need of  matching them by blood type compatibility and real world proximity

## Features

- **Blood Type Compatibility Matching** — Automatically finds donors compatible with a requested blood type for examplen O- can only receive O-, AB+ can receive from anyone
- **Distance Based Matching** — Matches donors within a 50km radius of a request using real latitude and longitude coordinates  with a graceful fallback to city text matching for records without coordinates yet
- **Full Donation Lifecycle** — Tracks a donation through `pending → accepted → completed`, with support for `declined` and `cancelled` paths
- **Hospital Verification** — Hospitals submit a registration number and license document; admins verify them with a full audit trail (`verified_by`, `verified_at`)
- **Donor Profiles** — Blood type, availability, location, date of birth, gender, and running total of completed donations
- **Donor ↔ Hospital Messaging** — In-app chat tied to a specific blood request, with automatic notifications on new messages
- **Notifications** — Donors and hospitals are notified on matches, fulfillments, cancellations, and new messages
- **Admin Endpoints** — List/cancel any request, list all donors/hospitals, verify hospitals, view platform-wide stats
- **JWT Authentication** — Token-based auth via `djangorestframework-simplejwt`
- **Auto-Generated API Docs** — OpenAPI/Swagger docs via `drf-spectacular`
- **Dockerized** — Runs locally or in production via Docker + `docker-compose`
- **CI Pipeline** — GitHub Actions runs the full test suite against PostgreSQL on every push

## Installation & Setup

### Prerequisites
- Python 3.12+
- PostgreSQL or SQLite for local development
- Docker & Docker Compose  for containerized setup

### Step 1: Clone the Repository
```bash
git clone https://github.com/favourkendi-dev/bloodmatch-backend.git
cd bloodmatch-backend
```


### Step 2: Create a Virtual Environment and activate it
```bash
pipenv install
pipenv shell
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy the example file and fill in real values:
```bash
cp .env.example .env
```

### Step 5: Run Migrations
```bash
python manage.py migrate
```

### Step 6: Create a Superuser  this is for Django Admin access
```bash
python manage.py createsuperuser
```

### Step 7: Run the Development Server
```bash
python manage.py runserver
```

Visit: `http://127.0.0.1:8000/`

### Alternative: Run with Docker
```bash
docker compose up --build
```
This starts the app together with a PostgreSQL database, applies migrations, and serves the API on `http://localhost:8000/`.

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/auth/login/` | POST | Log in, returns access + refresh tokens |
| `/api/auth/register/` | POST | Register a new user |
| `/api/donors/profile/` | GET, PATCH | View/update your own donor profile |
| `/api/hospitals/profile/` | GET, PATCH | View/update your own hospital profile |
| `/api/requests/` | GET, POST | List or create blood requests |
| `/api/requests/<id>/` | GET, PATCH | View/update a specific request |
| `/api/requests/<id>/matches/` | GET | Get compatible, nearby donors for a request |
| `/api/requests/<id>/select_donor/` | POST | Hospital selects a donor for the request |
| `/api/requests/<id>/accept/` | POST | Donor accepts a matched request |
| `/api/requests/<id>/decline/` | POST | Donor declines a matched request |
| `/api/requests/<id>/fulfill/` | POST | Hospital marks a request as fulfilled |
| `/api/requests/<id>/cancel/` | POST | Hospital cancels a request |
| `/api/requests/my_matches/` | GET | Donor views all requests they've been matched to |
| `/api/messages/` | GET, POST | View or send messages tied to a blood request |
| `/api/messages/<id>/read/` | POST | Mark a message as read |
| `/api/notifications/` | GET | List your notifications |
| `/api/admin/hospitals/` | GET | Admin-only: list all hospitals |
| `/api/admin/hospitals/<id>/verify/` | POST | Admin-only: verify a hospital |
| `/api/admin/donors/` | GET | Admin-only: list all donors |
| `/api/admin/requests/` | GET | Admin-only: list every request in the system |
| `/api/admin/requests/<id>/cancel/` | POST | Admin-only: force-cancel any request |
| `/api/admin/reports/` | GET | Admin-only: platform-wide stats |
| `/api/docs/` | GET | Interactive Swagger API documentation |

## Technologies Used
- Python 3.12 — Backend language
- Django 4.2 — Web framework
- Django REST Framework — API layer
- djangorestframework-simplejwt — JWT authentication
- PostgreSQL — Production database
- drf-spectacular — Auto-generated OpenAPI/Swagger docs
- Gunicorn — Production WSGI server
- Whitenoise — Static file serving in production
- django-cors-headers — Cross-origin support for the frontend
- Docker & Docker Compose — Containerized local/production environment
- GitHub Actions — CI pipeline  for running  tests on every push
- Render — Deployment platform

## Testing

Run the test suite:
```bash
python manage.py test
```

Check coverage:
```bash
coverage run --source='.' manage.py test
coverage report
```

## Author
Favour Kendi
