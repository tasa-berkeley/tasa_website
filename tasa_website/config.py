import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-only-not-a-secret')
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD_HASH = os.environ.get('ADMIN_PASSWORD_HASH', '')

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB uploads

    # Upload folders, as forward-slash paths relative to the package root.
    # These match the layout the pre-2026 site used, so image_url values
    # imported from the old database keep resolving.
    OFFICER_IMAGE_FOLDER = 'static/images/officers'
    FAMILY_IMAGE_FOLDER = 'static/images/families'
    TESTIMONIAL_IMAGE_FOLDER = 'static/images/testimonials'

    @staticmethod
    def database_uri(instance_path):
        path = os.environ.get('DATABASE_PATH') or os.path.join(instance_path, 'tasa_website.db')
        return 'sqlite:///' + os.path.abspath(path).replace('\\', '/')
