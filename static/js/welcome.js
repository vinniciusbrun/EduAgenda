/* 
   Welcome Screen Logic
   Ensures display only once per session.
*/

const WelcomeScreen = {
    overlay: null,
    btn: null,

    init() {
        this.overlay = document.getElementById('welcomeOverlay');
        const closeBtn = document.getElementById('welcomeCloseBtn');

        if (!this.overlay) return;

        // Verifica se o usuário já viu a tela nesta sessão
        const hasSeen = sessionStorage.getItem('welcomeSeen') === 'true';

        if (!hasSeen) {
            this.show();
        }

        if (closeBtn) {
            closeBtn.onclick = () => this.hide();
        }
    },

    show() {
        // Pequeno delay para garantir que o CSS carregou e a transição funcione
        setTimeout(() => {
            this.overlay.classList.add('active');
            document.body.style.overflow = 'hidden'; // Impede scroll atrás
        }, 100);
    },

    hide() {
        this.overlay.classList.remove('active');
        document.body.style.overflow = ''; // Restaura scroll
        sessionStorage.setItem('welcomeSeen', 'true');

        // Remove do DOM após a animação para performance
        setTimeout(() => {
            this.overlay.style.display = 'none';
        }, 800);
    }
};

// Iniciar quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => WelcomeScreen.init());
