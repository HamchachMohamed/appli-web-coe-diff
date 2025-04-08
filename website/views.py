from flask import Blueprint, jsonify, render_template, request, flash, redirect, url_for, make_response
from flask_login import login_required, current_user
from . import db
import numpy as np
from .security import validate_scientific_input, secure_headers

views = Blueprint('views', __name__)

# Fonction pour calculer le coefficient de diffusion
def compute_diffusion_coefficient(x_A, D_AB0, D_BA0, q_A, T, D_exp, q_B, a_BA, a_AB, ra, rb):
    # Fraction de solvant
    x_B = 1 - x_A
    # Tau
    tau_AB = np.exp(-a_AB / T)
    tau_BA = np.exp(-a_BA / T)
    tau_AA = 1
    tau_BB = 1

    # Lambda
    lambda_A = ra ** (1 / 3)
    lambda_B = rb ** (1 / 3)

    # Phi
    phi_A = x_A * lambda_A / (x_A * lambda_A + x_B * lambda_B)
    phi_B = x_B * lambda_B / (x_A * lambda_A + x_B * lambda_B)

    # Theta
    theta_A = (x_A * q_A) / (x_A * q_A + x_B * q_B)
    theta_B = (x_B * q_B) / (x_A * q_A + x_B * q_B)
    theta_BA = (theta_B * tau_BA) / (theta_A * tau_AA + theta_B * tau_BA)
    theta_AB = (theta_A * tau_AB) / (theta_A * tau_AB + theta_B * tau_BB)
    theta_AA = (theta_A * tau_AA) / (theta_A * tau_AA + theta_B * tau_BA)
    theta_BB = (theta_B * tau_BB) / (theta_A * tau_AB + theta_B * tau_BB)

    # L'équation de HSU-CHEN
    terme1 = (
        x_B * np.log(D_AB0)
        + x_A * np.log(D_BA0)
        + 2 * (x_A * np.log(x_A / phi_A) + x_B * np.log(x_B / phi_B))
        + 2 * x_A * x_B * ((phi_A / x_A) * (1 - (lambda_A / lambda_B)) + (phi_B / x_B) * (1 - (lambda_B / lambda_A)))
    )
    terme2 = (x_B * q_A) * (
        (1 - theta_BA ** 2) * np.log(tau_BA)
        + (1 - theta_BB ** 2) * tau_AB * np.log(tau_AB)
    ) + (x_A * q_B) * (
        (1 - theta_AB ** 2) * np.log(tau_AB)
        + (1 - theta_AA ** 2) * tau_BA * np.log(tau_BA)
    )

    ln_D_AB = terme1 + terme2
    D_AB = np.exp(ln_D_AB)
    # L'erreur
    error = (np.abs(D_AB - D_exp) / D_exp) * 100

    return D_AB, error

@views.route('/')
def landing():
    if current_user.is_authenticated:
        return redirect(url_for('views.home'))
    return render_template("landing.html", user=current_user)

# Page d'accueil après connexion
@views.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    return render_template("home.html", user=current_user)

# Page pour saisir les valeurs
@views.route('/page2', methods=['GET'])
@login_required
def page2():
    return render_template("calculate.html", user=current_user)

# Page pour afficher les résultats
@views.route('/page3', methods=['POST'])
@login_required
def page3():
    try:
        # Validation des entrées avec messages d'erreur spécifiques
        inputs = {
            'x_A': (request.form['x_A'].replace(',', '.'), 0, 1),
            'D_AB0': (request.form['D_AB0'], 0, None),
            'D_BA0': (request.form['D_BA0'], 0, None),
            'ra': (request.form['rA'], 0, None),
            'rb': (request.form['rB'], 0, None),
            'D_AB_exp': (request.form['D_AB_exp'], 0, None),
            'a_AB': (request.form['a_AB'], None, None),
            'a_BA': (request.form['a_BA'], None, None),
            'T': (request.form['T'], 0, None),
            'q_A': (request.form['q_A'], 0, None),
            'q_B': (request.form['q_B'], 0, None)
        }

        validated_inputs = {}
        for key, (value, min_val, max_val) in inputs.items():
            is_valid, num_value, error_msg = validate_scientific_input(value, min_val, max_val)
            if not is_valid:
                flash(f'Erreur pour {key}: {error_msg}', category='error')
                return redirect(url_for('views.page2'))
            validated_inputs[key] = num_value

        # Utilise les valeurs validées
        D_AB, error = compute_diffusion_coefficient(
            validated_inputs['x_A'],
            validated_inputs['D_AB0'],
            validated_inputs['D_BA0'],
            validated_inputs['q_A'],
            validated_inputs['T'],
            validated_inputs['D_AB_exp'],
            validated_inputs['q_B'],
            validated_inputs['a_BA'],
            validated_inputs['a_AB'],
            validated_inputs['ra'],
            validated_inputs['rb']
        )

        response = make_response(render_template(
            "result.html",
            D_AB=f"{D_AB:.3e}",
            error=f"{error:.2f}",
            user=current_user
        ))
        
        # Ajoute les headers de sécurité
        for key, value in secure_headers().items():
            response.headers[key] = value
            
        return response

    except ValueError as e:
        flash('Valeurs invalides. Veuillez entrer des nombres valides.', category='error')
        return redirect(url_for('views.page2'))
    except Exception as e:
        flash('Une erreur inattendue est survenue. Veuillez réessayer.', category='error')
        return redirect(url_for('views.page2'))