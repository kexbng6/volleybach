// Application Vue pour la page d'accueil
const app = Vue.createApp({
  data() {
    return {
      appName: 'Volleybach app v2.0',
      modes: [
        {
          id: 'realize-match',
          title: 'Réaliser un match',
          description: 'Créer un match en saisissant les réglages du streaming, les équipes et les joueurs.',
          icon: 'bi-pencil-square',
          route: '/setup'
        },
        {
          id: 'presetings',
          title: 'Charger un préréglage',
          description: 'Charger un préréglage de match pour démarrer rapidement.',
          icon: 'bi-file-earmark-text',
          route: '/presets'
        }
      ],
      connected: false
    }
  },
  methods: {
    checkVMixConnection() {
      // Cette fonction pourra être implémentée ultérieurement
      // pour vérifier la connexion à vMix
      fetch('/api/vmix-status')
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
  }
});

// Montage de l'application Vue
app.mount('#app');
