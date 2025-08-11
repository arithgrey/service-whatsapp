#!/bin/sh
# Ejecuta las migraciones si es necesario
echo "Microservice WhatsApp"
echo "Running makemigrations and migrate..."

python manage.py makemigrations
python manage.py makemigrations whatsapp notifications
python manage.py migrate

# Inicia el servidor con gunicorn (watchmedo temporalmente deshabilitado por compatibilidad)
echo "Starting the server with gunicorn..."
watchmedo auto-restart --directory=./ --pattern=*.py --recursive -- gunicorn -b 0.0.0.0:8080 app.wsgi:application
