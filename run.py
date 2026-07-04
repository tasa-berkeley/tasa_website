"""Local development entry point. Use wsgi.py + gunicorn in production."""
from tasa_website import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001)
