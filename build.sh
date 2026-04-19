#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input

python manage.py makemigrations accounts
python manage.py makemigrations students
python manage.py makemigrations teachers
python manage.py makemigrations fees
python manage.py makemigrations expenses
python manage.py makemigrations reports
python manage.py makemigrations core

python manage.py migrate --run-syncdb

# Auto create superuser if not exists
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@tsm.com',
        password='Admin@123',
        first_name='Admin',
        last_name='User',
    )
    print('Superuser created: admin / Admin@123')
else:
    print('Superuser already exists')
"
