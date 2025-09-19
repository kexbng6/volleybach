// Application Vue pour la page de configuration
// todo relire les fonctions d'init, de check, de set time et show notification
const setupApp = Vue.createApp({
  data() {
    return {
      // Configuration vMix
      vmixConfig: {
        host: '127.0.0.1',   // Adresse IP où tourne vMix
        port: 8088,          // Port API de vMix (8088 par défaut)
        apiKey: '',          // Clé API si configurée
      },
      // Configuration du stream
      streamConfig: {
        service:'Custom',
        url: '',             // Changé de streamURL à url pour correspondre à l'API
        name: '',            // Changé de streamName à name pour correspondre à l'API
        key: '',             // Changé de streamKey à key pour correspondre à l'API
        quality: 'High',     // Options: Low, Medium, High
        encoder: 'x264',     // Options: x264, NVENC, QuickSync
      },
      // Nouvel input en cours d'ajout
      newInput: {
        type: '',            // Changé de inputType à type pour correspondre à l'API
        name: '',            // Changé de title à name pour correspondre à l'API
        source: '',          // ID ou path de la source
        sourceName: ''       // Nom lisible de la source
      },
      // Nouvel input vMix à ajouter directement dans vMix
      newVmixInput: {
        sourceType: 'camera', // Type de source: camera, video, audio, blank
        sourceId: '',        // ID de la source sélectionnée
        sourceName: '',      // Nom de la source pour affichage
        isAddingInput: false // Flag pour indiquer si un ajout est en cours
      },
      // Liste des inputs configurés
      inputs: [],
      // Sources disponibles (inputs existants dans vMix)
      videoSources: [],      // Sources vidéo existantes
      audioSources: [],      // Sources audio existantes
      cameraSources: [],     // Sources caméra existantes
      blankSources: [],      // Sources blank existantes

      // Sources disponibles pour créer de nouveaux inputs dans vMix
      newCameraSources: [],  // Périphériques de capture disponibles
      newVideoSources: [],   // Options de sources vidéo
      newAudioSources: [],   // Options de sources audio
      newBlankSources: [],   // Options de sources blank

      socket: null,          // Pour la connexion WebSocket
      vmixConnected: false,  // Indique si vMix est connecté
      notifications: [],     // Pour stocker les notifications à afficher
      isLoadingSources: false, // Indique si les sources sont en cours de chargement
      isAddingVmixInput: false // Indique si un ajout d'input vMix est en cours
    };
  },
  computed: {
    // Vérifie si on peut ajouter un nouvel input
    canAddInput() {
      return this.newInput.type && this.newInput.name && this.newInput.source;
    },

    // Vérifie si on peut ajouter un nouvel input directement dans vMix
    canAddVmixInput() {
      return this.newVmixInput.sourceType && this.newVmixInput.sourceId && !this.isAddingVmixInput;
    }
  },
  methods: {
    // Initialisation de la connexion WebSocket
    initWebSocket() {
      try {
        this.socket = io();

        // Événements de connexion
        this.socket.on('connect', () => {
          console.log('WebSocket connecté');
        });

        this.socket.on('disconnect', () => {
          console.log('WebSocket déconnecté');
        });

        // Écoute des mises à jour des inputs
        this.socket.on('inputs_update', (data) => {
          console.log('Mise à jour des inputs reçue:', data);
          if (data.inputs) {
            this.inputs = data.inputs;
          }
        });

        // Écoute des mises à jour de statut vMix
        this.socket.on('vmix_status_update', (data) => {
          console.log('Mise à jour du statut vMix:', data);
          this.vmixConnected = data.connected;
          this.showNotification(
            data.connected ? 'vMix est maintenant connecté' : 'vMix est déconnecté',
            data.connected ? 'success' : 'warning'
          );
        });
      } catch (error) {
        console.error('Erreur lors de l\'initialisation du WebSocket:', error);
      }
      // Écoute des mises à jour de la configuration du stream
      this.socket.on('stream_config_update', (data) => {
        console.log('Mise à jour de la configuration du stream reçue:', data);
        if (data.config) {
          this.streamConfig = data.config;
          this.showNotification('Configuration du stream mise à jour', 'info');
        }
      });
    },

    // Vérification du statut de vMix
    checkVmixStatus() {
      fetch('/api/vmix-status')
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            const previousStatus = this.vmixConnected;
            this.vmixConnected = data.vmix_connected;

            // Notification seulement si le statut a changé
            if (previousStatus !== this.vmixConnected) {
              this.showNotification(
                this.vmixConnected ? 'vMix est connecté' : 'vMix est déconnecté',
                this.vmixConnected ? 'success' : 'warning'
              );
            }
          }
        })
        .catch(error => {
          console.error('Erreur lors de la vérification du statut vMix:', error);
        });
    },

    // Affiche une notification à l'utilisateur
    showNotification(message, type = 'info') {
      const notification = {
        id: Date.now(),
        message,
        type // info, success, warning, danger
      };

      this.notifications.push(notification);

      // Supprimer la notification après 5 secondes
      setTimeout(() => {
        const index = this.notifications.findIndex(n => n.id === notification.id);
        if (index !== -1) {
          this.notifications.splice(index, 1);
        }
      }, 5000);
    },

    // Sauvegarde la configuration du stream
    saveStreamConfig() {
      console.log('Sauvegarde de la configuration du stream:', this.streamConfig);

      // Envoi des données au backend
      fetch('/api/save-stream-config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(this.streamConfig)
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          this.showNotification('Configuration du stream enregistrée avec succès!', 'success');
        } else {
          this.showNotification('Erreur lors de l\'enregistrement: ' + data.message, 'danger');
        }
      })
      .catch(error => {
        console.error('Erreur:', error);
        this.showNotification('Une erreur est survenue lors de la sauvegarde.', 'danger');
      });
    },

    // Ajoute un nouvel input à la liste
    addInput() {
      if (this.canAddInput) {
        // Création d'une copie pour éviter les références
        const inputToAdd = {
          type: this.newInput.type,
          name: this.newInput.name,
          source: this.newInput.source,
          // On pourrait ajouter des détails supplémentaires ici
          sourceName: this.getSourceName(this.newInput.type, this.newInput.source)
        };

        this.inputs.push(inputToAdd);

        // Envoi au backend
        this.saveInputToBackend(inputToAdd);

        // Réinitialisation du formulaire
        this.newInput = {
          type: '',
          name: '',
          source: ''
        };
      }
    },

    // Supprime un input de la liste
    removeInput(index) {
      const inputToRemove = this.inputs[index];

      // Suppression côté backend
      fetch('/api/remove-input', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ inputId: index, input: inputToRemove })
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          // Suppression côté frontend
          this.inputs.splice(index, 1);
          this.showNotification('Input supprimé avec succès', 'success');
        } else {
          this.showNotification('Erreur lors de la suppression: ' + data.message, 'danger');
        }
      })
      .catch(error => {
        console.error('Erreur:', error);
        this.showNotification('Une erreur est survenue lors de la suppression.', 'danger');
      });
    },

    // Enregistre un input dans le backend
    saveInputToBackend(input) {
      fetch('/api/add-input', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(input)
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          this.showNotification('Input ajouté avec succès', 'success');
        } else {
          this.showNotification('Erreur lors de l\'ajout de l\'input: ' + data.message, 'danger');
          // On pourrait retirer l'input de la liste en cas d'erreur
        }
      })
      .catch(error => {
        console.error('Erreur:', error);
        this.showNotification('Une erreur est survenue lors de l\'ajout de l\'input.', 'danger');
      });
    },

    // Charge les sources disponibles pour créer de nouveaux inputs dans vMix
    loadAvailableInputSources() {
      this.isLoadingSources = true;

      fetch('/api/available-input-sources')
        .then(response => response.json())
        .then(data => {
          this.isLoadingSources = false;

          if (data.success) {
            this.newCameraSources = data.cameraSources || [];
            this.newVideoSources = data.videoSources || [];
            this.newAudioSources = data.audioSources || [];
            this.newBlankSources = data.blankSources || [];

            console.log('Sources disponibles pour nouveaux inputs:', {
              camera: this.newCameraSources,
              video: this.newVideoSources,
              audio: this.newAudioSources,
              blank: this.newBlankSources
            });

            this.showNotification('Sources disponibles chargées avec succès', 'success');
          } else {
            this.showNotification('Erreur: ' + (data.message || 'Impossible de charger les sources'), 'danger');
          }
        })
        .catch(error => {
          this.isLoadingSources = false;
          console.error('Erreur lors du chargement des sources disponibles:', error);
          this.showNotification('Erreur lors du chargement des sources disponibles.', 'warning');
        });
    },

    // Ajoute un nouvel input directement dans vMix
    addVmixInput() {
      if (!this.canAddVmixInput) return;

      this.isAddingVmixInput = true;

      // Préparation des données pour la requête
      const inputData = {
        sourceType: this.newVmixInput.sourceType,
        sourceId: this.newVmixInput.sourceId
      };

      // Trouver le nom de la source pour l'affichage
      const sourcesArray = this.getSourcesArrayForType(this.newVmixInput.sourceType, true);
      const selectedSource = sourcesArray.find(s => s.id === this.newVmixInput.sourceId);
      if (selectedSource) {
        inputData.sourceName = selectedSource.name;
      }

      console.log('Ajout d\'un nouvel input vMix:', inputData);

      // Envoi de la requête pour ajouter l'input dans vMix
      fetch('/api/add-vmix-input', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(inputData)
      })
      .then(response => response.json())
      .then(data => {
        this.isAddingVmixInput = false;

        if (data.success) {
          this.showNotification(`Input ${inputData.sourceName || 'inconnu'} ajouté avec succès dans vMix`, 'success');

          // Réinitialisation du formulaire
          this.newVmixInput = {
            sourceType: 'camera',
            sourceId: '',
            sourceName: ''
          };

          // Rafraîchissement des sources pour afficher le nouvel input
          this.refreshSources();
        } else {
          this.showNotification('Erreur lors de l\'ajout de l\'input dans vMix: ' + (data.message || 'Erreur inconnue'), 'danger');
        }
      })
      .catch(error => {
        this.isAddingVmixInput = false;
        console.error('Erreur:', error);
        this.showNotification('Une erreur est survenue lors de l\'ajout de l\'input dans vMix.', 'danger');
      });
    },

    // Fonction utilitaire pour obtenir le tableau de sources correspondant au type
    getSourcesArrayForType(type, isNewInput = false) {
      if (isNewInput) {
        // Sources pour nouveaux inputs
        switch (type) {
          case 'camera': return this.newCameraSources;
          case 'video': return this.newVideoSources;
          case 'audio': return this.newAudioSources;
          case 'blank': return this.newBlankSources;
          default: return [];
        }
      } else {
        // Sources existantes (inputs déjà dans vMix)
        switch (type) {
          case 'camera': return this.cameraSources;
          case 'video': return this.videoSources;
          case 'audio': return this.audioSources;
          case 'blank': return this.blankSources;
          default: return [];
        }
      }
    },

    // Met à jour la valeur sourceName lorsqu'un sourceId est sélectionné
    updateSourceName() {
      const sourcesArray = this.getSourcesArrayForType(this.newVmixInput.sourceType, true);
      const selectedSource = sourcesArray.find(s => s.id === this.newVmixInput.sourceId);
      if (selectedSource) {
        this.newVmixInput.sourceName = selectedSource.name;
      }
    },

    // Obtient le nom d'une source à partir de son ID
    getSourceName(type, sourceId) {
      // Version améliorée qui prend en compte tous les types de sources
      const sourcesArray = this.getSourcesArrayForType(type);
      const source = sourcesArray.find(s => s.id === sourceId);
      return source ? source.name : 'Source inconnue';
    },

    // Charge les données existantes depuis le backend
    loadExistingData() {
      // Chargement de la configuration du stream
      fetch('/api/stream-config')
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            this.streamConfig = data.config;
          }
        })
        .catch(error => {
          console.error('Erreur lors du chargement de la configuration:', error);
          this.showNotification('Erreur lors du chargement de la configuration du stream.', 'warning');
        });

      // Chargement des inputs existants
      fetch('/api/inputs')
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            this.inputs = data.inputs;
          }
        })
        .catch(error => {
          console.error('Erreur lors du chargement des inputs:', error);
          this.showNotification('Erreur lors du chargement des inputs.', 'warning');
        });

      // Chargement des sources disponibles (à implémenter plus tard)
      fetch('/api/available-sources')
          .then(response => response.json())
          .then(data => {
            if (data.success) {
              if (data.videoSources) this.videoSources = data.videoSources;
              if (data.audioSources) this.audioSources = data.audioSources;
              if (data.blankSources) this.blankSources = data.blankSources;
            }
          })
          .catch(error => {
            console.error('Erreur lors du chargement des sources disponibles', error);
            this.showNotification('Erreur lors du chargement des sources disponibles.', 'warning');
          });

      // Chargement des sources disponibles pour nouveaux inputs
      this.loadAvailableInputSources();
    },

    // Rafraîchit la liste des sources disponibles depuis l'API
    refreshSources() {
      this.isLoadingSources = true;

      // Rafraîchissement des inputs existants
      fetch('/api/available-sources')
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            if (data.videoSources) this.videoSources = data.videoSources;
            if (data.audioSources) this.audioSources = data.audioSources;
            if (data.cameraSources) this.cameraSources = data.cameraSources;
            if (data.blankSources) this.blankSources = data.blankSources;
          } else {
            console.error('Erreur lors du rafraîchissement des sources existantes:', data.message);
          }

          // Ensuite, rafraîchir les sources pour nouveaux inputs
          return fetch('/api/available-input-sources');
        })
        .then(response => response.json())
        .then(data => {
          this.isLoadingSources = false;

          if (data.success) {
            this.newCameraSources = data.cameraSources || [];
            this.newVideoSources = data.videoSources || [];
            this.newAudioSources = data.audioSources || [];
            this.newBlankSources = data.blankSources || [];

            this.showNotification('Sources mises à jour', 'success');
          } else {
            this.showNotification('Erreur lors de la mise à jour des sources: ' + (data.message || ''), 'danger');
          }
        })
        .catch(error => {
          this.isLoadingSources = false;
          console.error('Erreur lors du rafraîchissement des sources:', error);
          this.showNotification('Une erreur est survenue lors du rafraîchissement des sources.', 'danger');
        });
    }
  },
  mounted() {
    // Chargement des données existantes au démarrage
    this.loadExistingData();
    this.initWebSocket();

    // Vérification initiale du statut de vMix
    this.checkVmixStatus();

    // Vérification périodique du statut de vMix
    setInterval(() => {
      this.checkVmixStatus();
    }, 30000); // Vérification toutes les 30 secondes
  }
});

// Montage de l'application Vue
setupApp.mount('#setup-app');
