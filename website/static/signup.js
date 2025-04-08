document.getElementById('signupForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const email = formData.get('email');
    const firstName = formData.get('firstName');
    const password1 = formData.get('password1');
    const password2 = formData.get('password2');
    
    try {
        const response = await fetch('/validate-password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                firstName: firstName,
                password: password1,
                password2: password2
            })
        });
        
        const result = await response.json();
        if (result.valid) {
            this.submit();
        } else {
            // Effacer seulement les mots de passe
            document.getElementById('password1').value = '';
            document.getElementById('password2').value = '';
            document.getElementById('password1').focus();
            
            // Afficher le flash message avec le message d'erreur du serveur
            const flashContainer = document.getElementById('flash-messages');
            if (flashContainer) {
                const alertDiv = document.createElement('div');
                alertDiv.className = 'alert alert-light-danger alert-dismissible fade show';
                alertDiv.style.backgroundColor = '#ffe6e6';  // Rouge clair
                alertDiv.style.color = '#dc3545';  // Rouge foncé pour le texte
                alertDiv.style.border = '1px solid #dc3545';
                alertDiv.innerHTML = `
                    ${result.message}
                    <button type="button" class="close" data-dismiss="alert">
                        <span>&times;</span>
                    </button>
                `;
                flashContainer.appendChild(alertDiv);
                
                // Auto-disparition après 5 secondes
                setTimeout(() => {
                    alertDiv.remove();
                }, 5000);
            }
        }
    } catch (error) {
        console.error('Erreur:', error);
    }
});
