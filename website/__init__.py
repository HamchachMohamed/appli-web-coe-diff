from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from os import path
from flask_login import LoginManager
from flask_mail import Mail, Message
from dotenv import load_dotenv

load_dotenv()  # Charger les variables d'environnement

DB_NAME = "database.db"
db = SQLAlchemy()
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'hjshjhdjah kjshkjdhjs'
    
    # Configuration base de données
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, DB_NAME)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configuration email mise à jour
    app.config.update(
        MAIL_SERVER='smtp.gmail.com',
        MAIL_PORT=587,
        MAIL_USE_TLS=True,
        MAIL_USERNAME=os.getenv('MAIL_USERNAME'),
        MAIL_PASSWORD=os.getenv('MAIL_PASSWORD'),
        MAIL_DEFAULT_SENDER=os.getenv('MAIL_DEFAULT_SENDER')
    )
    
    mail.init_app(app)
    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User  # Supprimer l'import de Note

    with app.app_context():
        try:
            if not os.path.exists(db_path):
                db.create_all()
                print("Nouvelle base de données créée!")
            else:
                print("Base de données existante trouvée.")
        except Exception as e:
            print(f"Erreur base de données: {str(e)}")

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."
    login_manager.login_message_category = "info"
    login_manager.init_app(app)

    from .models import User  # Import the User model

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app


def create_database(app):
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, DB_NAME)
    if not os.path.exists(db_path):
        with app.app_context():
            try:
                db.create_all()
                print("Base de données et tables créées avec succès!")
            except Exception as e:
                print(f"Erreur lors de la création de la base de données : {e}")
            print(f'Base de données créée à: {db_path}')
    return True