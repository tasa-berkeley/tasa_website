"""Production entry point: gunicorn wsgi:app"""
from tasa_website import create_app

app = create_app()
