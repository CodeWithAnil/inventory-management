from logging.handlers import RotatingFileHandler
from flask import Flask
import logging
from flask_sqlalchemy import SQLAlchemy
from flask_mysqldb import MySQL


# Initialize extensions
db = SQLAlchemy()
mysql = MySQL()

def create_app(config_name='default'):
    app = Flask(__name__)
    
    general_log_handler = RotatingFileHandler('logs/general.log', maxBytes=10000, backupCount=3)
    general_log_handler.setLevel(logging.INFO)
    general_formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )
    general_log_handler.setFormatter(general_formatter)

    # Set up error logging
    error_log_handler = RotatingFileHandler('logs/error.log', maxBytes=10000, backupCount=3)
    error_log_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )
    error_log_handler.setFormatter(error_formatter)

    # Add handlers to the app logger
    app.logger.addHandler(general_log_handler)
    app.logger.addHandler(error_log_handler)
    app.logger.setLevel(logging.INFO)


    if config_name == 'default':
        app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:anil%40123@localhost/inventory'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SECRET_KEY'] = 'anil'
        app.config['MYSQL_HOST'] = 'localhost'
        app.config['MYSQL_USER'] = 'root'
        app.config['MYSQL_PASSWORD'] = 'anil@123'
        app.config['MYSQL_DB'] = 'inventory'
    elif config_name == 'testing':
        app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:anil%40123@localhost/unittest_inventory'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SECRET_KEY'] = 'test_secret'
        app.config['TESTING'] = True

    # Initialize extensions with the app
    db.init_app(app)
    if config_name == 'default':
        mysql.init_app(app)

    # Import blueprints and register them
    from auth.routes import auth_bp


    app.register_blueprint(auth_bp)


    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
