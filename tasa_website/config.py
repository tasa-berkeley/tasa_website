import os


class Config:
    # Only needed if flashing/sessions are ever added; harmless otherwise.
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-only-not-a-secret')
