from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify, session  # Ajouter cet import en haut
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, mail, create_app  # Import create_app to access app
from flask_login import login_user, login_required, logout_user, current_user
from flask_mail import Message
import traceback
import uuid
from smtplib import SMTPException
import ssl
import re  # Ajouter en haut du fichier avec les autres imports
import random
from datetime import datetime, timedelta
import secrets

auth = Blueprint('auth', __name__)

def generate_reset_code():
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])

@auth.route('/login', methods=['GET', 'POST'])
def login():
    from .models import User  # Import here to avoid circular import
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html", user=current_user)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


def password_check(password):
    """
    Vérifie que le mot de passe respecte les critères de sécurité
    """
    if len(password) < 7:
        return False, "Le mot de passe doit contenir au moins 7 caractères."
    if not re.search(r"[A-Z]", password):
        return False, "Le mot de passe doit contenir au moins une lettre majuscule."
    if not re.search(r"[a-z]", password):
        return False, "Le mot de passe doit contenir au moins une lettre minuscule."
    if not re.search(r"\d", password):
        return False, "Le mot de passe doit contenir au moins un chiffre."
    if not re.search(r"[ !@#$%&'()*+,-./[\\\]^_`{|}~"+r'"]', password):
        return False, "Le mot de passe doit contenir au moins un caractère spécial."
    return True, "Mot de passe valide"

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    from .models import User
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        # Sauvegarder les données dans la session
        session['signup_email'] = email
        session['signup_firstname'] = first_name

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Cet email existe déjà.', category='error')
        elif len(email) < 4:
            flash('Email doit contenir plus de 3 caractères.', category='error')
        elif len(first_name) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif password1 != password2:
            flash('Les mots de passe ne correspondent pas.', category='error')
        else:
            is_valid, msg = password_check(password1)
            if not is_valid:
                flash(msg, category='error')
            else:
                new_user = User(email=email, first_name=first_name, password=generate_password_hash(
                    password1, method='pbkdf2:sha256'))
                db.session.add(new_user)
                db.session.commit()
                session.pop('signup_email', None)
                session.pop('signup_firstname', None)
                login_user(new_user, remember=True)
                flash('Compte créé avec succès!', category='success')
                return redirect(url_for('views.home'))

    return render_template("sign_up.html", 
        user=current_user,
        email=session.get('signup_email', ''),
        firstName=session.get('signup_firstname', '')
    )

@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    from .models import User
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            try:
                reset_code = generate_reset_code()
                user.reset_code = reset_code
                user.reset_code_timestamp = datetime.utcnow()
                db.session.commit()
                
                msg = Message(
                    subject='[CD App] Code de réinitialisation de mot de passe',
                    recipients=[email]
                )
                
                # Corps HTML de l'email
                msg.html = f'''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #333;">Réinitialisation de mot de passe</h2>
                    <p>Bonjour {user.first_name},</p>
                    <p>Vous avez demandé la réinitialisation de votre mot de passe. 
                       Voici votre code de vérification :</p>
                    <div style="background-color: #f5f5f5; padding: 15px; text-align: center; 
                                font-size: 24px; font-weight: bold; color: #4a90e2; 
                                border-radius: 5px; margin: 20px 0;">
                        {reset_code}
                    </div>
                    <p>Ce code expirera dans 10 minutes.</p>
                    <p>Si vous n'avez pas demandé cette réinitialisation, 
                       veuillez ignorer cet email.</p>
                    <hr style="border: 1px solid #eee; margin: 20px 0;">
                    <p style="color: #666; font-size: 12px;">
                        Ceci est un email automatique, merci de ne pas y répondre.
                    </p>
                </div>
                '''
                
                # Version texte de l'email
                msg.body = f'''
                Réinitialisation de mot de passe
                
                Bonjour {user.first_name},
                
                Vous avez demandé la réinitialisation de votre mot de passe.
                Voici votre code de vérification : {reset_code}
                
                Ce code expirera dans 10 minutes.
                
                Si vous n'avez pas demandé cette réinitialisation, veuillez ignorer cet email.
                '''
                
                mail.send(msg)
                print(f"Email envoyé avec succès à {email} avec le code {reset_code}")
                flash('Un code de réinitialisation a été envoyé à votre adresse email.', 'success')
                return redirect(url_for('auth.verify_reset_code', email=email))
                
            except Exception as e:
                print(f"Erreur d'envoi d'email: {str(e)}")
                db.session.rollback()
                flash("Erreur lors de l'envoi de l'email. Veuillez réessayer.", 'error')
                    
        else:
            flash('Aucun compte associé à cet email.', 'error')
    
    return render_template('forgot_password.html', user=current_user)

@auth.route('/verify-reset-code/<email>', methods=['GET', 'POST'])
def verify_reset_code(email):
    from .models import User
    if request.method == 'POST':
        code = request.form.get('code')
        user = User.query.filter_by(email=email).first()
        
        if user and user.reset_code == code and user.reset_code_timestamp:
            # Check if code hasn't expired (10 minutes)
            expiration_time = user.reset_code_timestamp + timedelta(minutes=10)
            if datetime.utcnow() < expiration_time:
                # Generate reset token
                reset_token = secrets.token_urlsafe(32)
                user.reset_token = reset_token
                db.session.commit()
                # Redirect to reset password page with token
                return redirect(url_for('auth.reset_password', token=reset_token))
            else:
                flash('Code expiré. Veuillez demander un nouveau code.', 'error')
        else:
            flash('Code invalide', 'error')
    
    return render_template('verify_reset_code.html', email=email, user=current_user)

@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    from .models import User
    user = User.query.filter_by(reset_token=token).first()
    
    if not user:
        flash('Lien invalide ou expiré.', category='error')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        new_password = request.form.get('password')  # Changed from password1
        
        if len(new_password) < 7:
            flash('Le mot de passe doit contenir au moins 7 caractères.', category='error')
        else:
            user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
            user.reset_token = None
            db.session.commit()
            flash('Mot de passe réinitialisé avec succès!', category='success')
            return redirect(url_for('auth.login'))
            
    return render_template('reset_password.html', user=current_user)

@auth.route('/validate-password', methods=['POST'])
def validate_password():
    data = request.json
    password = data.get('password')
    password2 = data.get('password2')
    
    if password != password2:
        return jsonify({
            'valid': False,
            'message': 'Les mots de passe ne correspondent pas.'
        })
        
    is_valid, msg = password_check(password)
    if not is_valid:
        return jsonify({
            'valid': False,
            'message': 'Le mot de passe doit contenir au moins une lettre majuscule, une lettre minuscule, un chiffre et un caractère spécial.'
        })
        
    return jsonify({
        'valid': True,
        'message': 'Mot de passe valide'
    })

def generate_verification_code():
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])

@auth.route('/verify-code', methods=['GET', 'POST'])
def verify_code():
    from .models import User  # Import User model to avoid "User is not defined" error
    if request.method == 'POST':
        code = request.form.get('code')
        new_password = request.form.get('new_password')
        
        user = User.query.filter_by(reset_code=code).first()
        if user and user.reset_code_timestamp:
            if datetime.utcnow() - user.reset_code_timestamp < timedelta(minutes=10):
                user.password = generate_password_hash(new_password, method='sha256')
                user.reset_code = None
                user.reset_code_timestamp = None
                db.session.commit()
                flash('Mot de passe modifié avec succès!', 'success')
                return redirect(url_for('auth.login'))
            else:
                flash('Code expiré. Veuillez demander un nouveau code.', 'error')
        else:
            flash('Code invalide.', 'error')
    
    return render_template("verify_code.html")