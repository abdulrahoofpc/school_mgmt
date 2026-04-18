# SchoolMS — School Management System

A production-ready School Management System with Accounting built with Django + Django REST Framework.

## Tech Stack
- **Backend**: Python Django 4.2 + Django REST Framework
- **Frontend**: Django Templates + Bootstrap-free custom CSS (dark theme)
- **Database**: PostgreSQL
- **Auth**: JWT (API) + Django Sessions (Web)
- **Charts**: Chart.js

## Modules
| Module | Features |
|--------|----------|
| Users | Custom User model, RBAC (Admin/Teacher/Accountant/Student), JWT |
| Students | CRUD, search, filter by class/section, pagination |
| Teachers | CRUD, subject management, salary structure |
| Fees | Fee structure per student, term-wise breakdown, payment tracking |
| Payments | Record payments, receipt generation, print-ready receipts |
| Salary | Monthly salary records, paid/unpaid tracking |
| Expenses | Categorized expenses, date/category filters |
| Reports | Fee report, Salary report, Expense report, Financial summary |
| Dashboard | Stats cards, income vs expense chart (Chart.js), recent payments |

## Quick Start

### 1. Prerequisites
- Python 3.10+
- PostgreSQL 14+

### 2. Setup
```bash
# Clone / extract project
cd school_mgmt

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and edit environment file
cp .env.example .env
# Edit .env with your DB credentials and secret key
```

### 3. Database
```bash
# Create PostgreSQL database
psql -U postgres -c "CREATE DATABASE school_mgmt;"

# Run migrations
python manage.py makemigrations
python manage.py migrate
```

### 4. Seed Sample Data
```bash
python manage.py seed_data
```
This creates:
- 3 staff users (admin, teacher1, accountant1)
- 8 teachers with salary records
- ~50 students across classes 5–8
- Fee structures + payment records
- 10 sample expenses

### 5. Run
```bash
python manage.py runserver
```
Open http://127.0.0.1:8000

## Login Credentials
| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin123` |
| Teacher | `teacher1` | `teacher123` |
| Accountant | `accountant1` | `acc123` |

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/accounts/token/` | Get JWT token |
| POST | `/api/accounts/token/refresh/` | Refresh token |
| GET | `/api/accounts/me/` | Current user |
| GET/POST | `/api/students/` | Students CRUD |
| GET/POST | `/api/teachers/` | Teachers CRUD |
| GET/POST | `/api/fees/structures/` | Fee structures |
| GET/POST | `/api/fees/payments/` | Payments |
| GET/POST | `/api/expenses/` | Expenses |

## Project Structure
```
school_mgmt/
├── accounts/          # User management, auth
├── students/          # Student CRUD
├── teachers/          # Teacher + salary management
├── fees/              # Fee structures + payments
├── expenses/          # Expense tracking
├── reports/           # Report views
├── core/              # Dashboard + seed command
├── school_mgmt/       # Django settings, root URLs
├── templates/         # All HTML templates
├── static/            # Static files
├── requirements.txt
├── .env.example
└── README.md
```

## Production Deployment Notes
1. Set `DEBUG=False` in `.env`
2. Set a strong `SECRET_KEY`
3. Set `ALLOWED_HOSTS` to your domain
4. Run `python manage.py collectstatic`
5. Use gunicorn + nginx in production
6. Consider using environment variables instead of `.env` file

## Fee Structure Fields
- Admission Fee
- Term 1, 2, 3 Fee
- Snacks Fee
- Book Fee
- Uniform Fee

## Expense Categories
- Program, Stationary, Fixed Asset, Gift, Travelling, Salary, Maintenance, Other
