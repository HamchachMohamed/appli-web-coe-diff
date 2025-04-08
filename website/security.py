import re
from html import escape
from urllib.parse import quote
import bleach

def sanitize_input(text):
    """Nettoie les entrées textuelles des caractères dangereux"""
    if not isinstance(text, str):
        return text
    return bleach.clean(str(text), strip=True)

def validate_email(email):
    """Valide le format d'une adresse email"""
    if not email or len(email) > 150:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_name(name):
    """Valide un nom (prénom ou nom de famille)"""
    if not name or len(name) > 150:
        return False
    return bool(re.match(r'^[a-zA-ZÀ-ÿ\s\'-]{2,}$', name))

def sanitize_numeric(value):
    """Nettoie et valide les entrées numériques"""
    if isinstance(value, (int, float)):
        return value
    try:
        # Remplace la virgule par un point pour la notation française
        clean_value = str(value).replace(',', '.')
        # Vérifie si c'est une notation scientifique
        if 'e' in clean_value.lower():
            return float(clean_value)
        # Vérifie si c'est un nombre décimal
        if '.' in clean_value:
            return float(clean_value)
        return int(clean_value)
    except (ValueError, TypeError):
        return None

def validate_password_strength(password):
    """
    Vérifie la force du mot de passe avec des critères stricts
    Retourne (bool, str) : (validité, message d'erreur)
    """
    if len(password) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères"
    
    if not re.search(r"[A-Z]", password):
        return False, "Le mot de passe doit contenir au moins une majuscule"
    
    if not re.search(r"[a-z]", password):
        return False, "Le mot de passe doit contenir au moins une minuscule"
    
    if not re.search(r"\d", password):
        return False, "Le mot de passe doit contenir au moins un chiffre"
    
    if not re.search(r"[ !@#$%^&*(),.?\":{}|<>]", password):
        return False, "Le mot de passe doit contenir au moins un caractère spécial"
    
    return True, "Mot de passe valide"

def secure_headers():
    """Retourne un dictionnaire de headers de sécurité recommandés"""
    return {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';",
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Referrer-Policy': 'strict-origin-when-cross-origin'
    }

def validate_scientific_input(value, min_val=None, max_val=None):
    """
    Valide les entrées scientifiques (nombres, notation scientifique)
    Retourne (bool, float|None, str) : (validité, valeur convertie, message d'erreur)
    """
    try:
        # Nettoie d'abord l'entrée
        clean_value = str(value).strip().lower()
        
        # Vérifie si c'est en notation scientifique
        if 'e' in clean_value:
            num = float(clean_value)
        else:
            # Remplace la virgule par un point
            clean_value = clean_value.replace(',', '.')
            num = float(clean_value)

        # Vérifie les limites si spécifiées
        if min_val is not None and num < min_val:
            return False, None, f"La valeur doit être supérieure à {min_val}"
        if max_val is not None and num > max_val:
            return False, None, f"La valeur doit être inférieure à {max_val}"
            
        return True, num, ""
    except (ValueError, TypeError):
        return False, None, "Valeur numérique invalide"
