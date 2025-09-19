/**
 * Système de notifications pour l'application Volleyball Streaming Manager
 * Gère l'affichage des notifications temporaires à l'utilisateur
 */

// todo review all this code

// Script de base pour les notifications
const notificationApp = Vue.createApp({
    data() {
        return {
            notifications: [],
            nextId: 0
        }
    },
    methods: {
        addNotification(message, type = 'info') {
            const id = this.nextId++;
            this.notifications.push({ id, message, type });
            setTimeout(() => {
                this.notifications = this.notifications.filter(n => n.id !== id);
            }, 5000);
        }
    },
    mounted() {
        // Écoute des événements de notification depuis le WebSocket
        window.addEventListener('notification', (event) => {
            this.addNotification(event.detail.message, event.detail.type);
        });
    }
}).mount('#notifications');

/**
 * Fonction utilitaire pour déclencher une notification
 * @param {string} message - Le message à afficher
 * @param {string} type - Le type de notification (info, success, warning, danger)
 */
function showNotification(message, type = 'info') {
    window.dispatchEvent(new CustomEvent('notification', {
        detail: { message, type }
    }));
}
