from flask import Flask, session, render_template
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    if not os.path.exists(app.instance_path):
        try: os.makedirs(app.instance_path)
        except OSError as e: app.logger.error(f"Error creating instance folder: {e}")

    uploads_path = app.config['UPLOAD_FOLDER']
    images_path = os.path.join(uploads_path, 'images')
    materials_path = os.path.join(uploads_path, 'materials')
    for path in [uploads_path, images_path, materials_path]:
         if not os.path.exists(path):
            try: os.makedirs(path); app.logger.info(f"Created upload folder: {path}")
            except OSError as e: app.logger.error(f"Error creating upload folder {path}: {e}")

    from app.main.routes import main_bp
    app.register_blueprint(main_bp)

    from app.auth.routes import auth_bp
    app.register_blueprint(auth_bp)

    from app.courses.routes import courses_bp
    app.register_blueprint(courses_bp)

    from app import errors

    @app.context_processor
    def inject_current_year():
        return {'current_year': datetime.utcnow().year}

    @app.before_request
    def make_session_permanent():
        session.permanent = True
        app.permanent_session_lifetime = app.config['PERMANENT_SESSION_LIFETIME']

    app.logger.info('Flask application created successfully.')
    return app

from app import models