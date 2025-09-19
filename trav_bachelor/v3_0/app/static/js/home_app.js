// Application Vue pour la page d'accueil
const app = Vue.createApp({
  data() {
    return {
      appName: 'Volleybach app v3.0',
      modes: [
        {
          id: 'setup-team',
          title: 'Configuration des équipes',
          description: 'Configurer les équipes, les joueurs et les statistiques pour le match.',
          icon: 'bi-people-fill',
          route: '/team-setup'
        },
        {
          id: 'setup-live',
          title: 'Configuration du direct',
          description: 'Configurer les paramètres de diffusion en direct.',
          icon: 'bi-camera-video-fill',
          route: '/live-setup'
        },
        {
          id: 'live-broadcast',
          title: 'Diffusion en direct',
          description: 'Gérer la diffusion en direct avec les commandes de score et de replay.',
          icon: 'bi-broadcast',
          route: '/live-broadcast'
        },
        {
          id: 'settings',
          title: 'Paramètres',
          description: 'Configurer les paramètres généraux de l\'application.',
          icon: 'bi-gear-fill',
          route: '/settings'
        }
      ],
      connected: false
    }
  },
  methods: {
    checkVMixConnection() {
      fetch('/api/vmix/status')
        .then(response => response.json())
        .then(data => {
          this.connected = data.connected;
        })
        .catch(error => {
          console.error('Erreur de vérification vMix:', error);
          this.connected = false;
        });
    }
  },
  mounted() {
    // Vérification initiale de la connexion vMix
    this.checkVMixConnection();

    // Mise à jour périodique du statut de connexion
    setInterval(() => {
      this.checkVMixConnection();
    }, 180000); // Vérifier toutes les 3 minutes
  }
});

// Montage de l'application Vue
app.mount('#app');
