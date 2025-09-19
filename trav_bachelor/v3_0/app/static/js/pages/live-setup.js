/**
 * Application de configuration du streaming live pour Volleyball Streaming Manager
 * Gère la connexion avec vMix, la configuration des entrées et le contrôle du streaming
 */

// todo review all this code

// Application Vue pour la configuration du streaming live
const liveSetupApp = Vue.createApp({
    data() {
        return {
            vmixHost: '127.0.0.1',
            vmixPort: 8088,
            vmixConnected: false,
            vmixInputs: [],
            streamingStatus: false,
            recordingStatus: false,
            matchInfo: {
                eventName: '',
                location: '',
                date: new Date().toISOString().split('T')[0],
                time: new Date().toTimeString().split(' ')[0].substring(0, 5),
                format: '5'
            },
            matchTeams: {
                teamA: null,
                teamB: null
            },
            overlayConfig: {
                scoreboardInput: '',
                playerDetailsInput: '',
                teamRosterInput: '',
                timeoutInput: '',
                thumbnailInput: '',
                showThumbnailAtStart: true
            },
            thumbnailFile: null,
            thumbnailPreview: null,
            socket: null
        };
    },
    methods: {
        // Connexion vMix
        async checkVmixConnection() {
            try {
                const response = await fetch(`/api/vmix/check-connection`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        host: this.vmixHost,
                        port: this.vmixPort
                    })
                });

                const result = await response.json();
                this.vmixConnected = result.connected;

                if (this.vmixConnected) {
                    this.showNotification('Connexion à vMix établie', 'success');
                    this.loadVmixInputs();
                    this.updateVmixStatus();
                } else {
                    this.showNotification('Connexion à vMix échouée', 'danger');
                }
            } catch (error) {
                console.error('Erreur:', error);
                this.showNotification('Erreur de connexion au serveur', 'danger');
                this.vmixConnected = false;
            }
        },

        async loadVmixInputs() {
            if (!this.vmixConnected) return;

            try {
                const response = await fetch(`/api/vmix/inputs`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        host: this.vmixHost,
                        port: this.vmixPort
                    })
                });

                const result = await response.json();
                this.vmixInputs = result.inputs || [];
            } catch (error) {
                console.error('Erreur:', error);
                this.showNotification('Erreur lors du chargement des entrées vMix', 'danger');
            }
        },

        async updateVmixStatus() {
            if (!this.vmixConnected) return;

            try {
                const response = await fetch(`/api/vmix/status`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        host: this.vmixHost,
                        port: this.vmixPort
                    })
                });

                const result = await response.json();
                this.streamingStatus = result.streaming || false;
                this.recordingStatus = result.recording || false;
            } catch (error) {
                console.error('Erreur:', error);
                this.showNotification('Erreur lors de la récupération du statut vMix', 'danger');
            }
        },

        // Gestion des entrées vMix
        async previewInput(inputId) {
            if (!this.vmixConnected) return;

            try {
                await fetch(`/api/vmix/preview-input`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        host: this.vmixHost,
                        port: this.vmixPort,
                        input: inputId
                    })
                });

                this.showNotification(`Aperçu de l'entrée ${inputId}`, 'info');
            } catch (error) {
                console.error('Erreur:', error);
                this.showNotification('Erreur lors de l\'aperçu de l\'entrée', 'danger');
            }
        },

        async setActiveInput(inputId) {
            if (!this.vmixConnected) return;

            try {
                await fetch(`/api/vmix/set-active-input`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        host: this.vmixHost,
                        port: this.vmixPort,
                        input: inputId
                    })
                });

                this.showNotification(`Entrée ${inputId} activée`, 'success');
            } catch (error) {
                console.error('Erreur:', error);
                this.showNotification('Erreur lors de l\'activation de l\'entrée', 'danger');
            }
        },

        // Gestion du streaming
        async toggleStreaming() {
            if (!this.vmixConnected) return;

            try {
                await fetch(`/api/vmix/toggle-streaming`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        host: this.vmixHost,
                        port: this.vmixPort,
                        action: this.streamingStatus ? 'stop' : 'start'
                    })
                });

                this.streamingStatus = !this.streamingStatus;
                this.showNotification(`Streaming ${this.streamingStatus ? 'démarré' : 'arrêté'}`, this.streamingStatus ? 'success' : 'warning');
            } catch (error) {
                console.error('Erreur:', error);
                this.showNotification('Erreur lors du contrôle du streaming', 'danger');
            }
        },

        async toggleRecording() {
            if (!this.vmixConnected) return;

            try {
                await fetch(`/api/vmix/toggle-recording`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        host: this.vmixHost,
                        port: this.vmixPort,
                        action: this.recordingStatus ? 'stop' : 'start'
                    })
                });

                this.recordingStatus = !this.recordingStatus;
                this.showNotification(`Enregistrement ${this.recordingStatus ? 'démarré' : 'arrêté'}`, this.recordingStatus ? 'success' : 'warning');
            } catch (error) {
                console.error('Erreur:', error);
                this.showNotification('Erreur lors du contrôle de l\'enregistrement', 'danger');
            }
        },

        // Gestion des médias
        handleThumbnailUpload(event) {
            this.thumbnailFile = event.target.files[0];

            // Créer un aperçu de l'image
            if (this.thumbnailFile) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    this.thumbnailPreview = e.target.result;
                };
                reader.readAsDataURL(this.thumbnailFile);
            }
        },

        // Contrôles divers
        goToBroadcastPage() {
            window.location.href = "/core/live_broadcast";
        },

        async saveConfiguration() {
            try {
                // Préparer les données pour l'envoi
                const formData = new FormData();
                formData.append('matchInfo', JSON.stringify(this.matchInfo));
                formData.append('overlayConfig', JSON.stringify(this.overlayConfig));
                formData.append('vmixConfig', JSON.stringify({
                    host: this.vmixHost,
                    port: this.vmixPort
                }));

                if (this.thumbnailFile) {
                    formData.append('thumbnail', this.thumbnailFile);
                }

                const response = await fetch('/api/match/save-configuration', {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    this.showNotification('Configuration enregistrée avec succès', 'success');
                } else {
                    const error = await response.json();
                    this.showNotification(`Erreur: ${error.message || 'Erreur inconnue'}`, 'danger');
                }
            } catch (error) {
                console.error('Erreur:', error);
                this.showNotification('Erreur de connexion au serveur', 'danger');
            }
        },

        async testOverlays() {
            if (!this.vmixConnected) return;

            try {
                await fetch(`/api/vmix/test-overlays`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        host: this.vmixHost,
                        port: this.vmixPort,
                        overlayConfig: this.overlayConfig
                    })
                });

                this.showNotification('Test des overlays effectué', 'info');
            } catch (error) {
                console.error('Erreur:', error);
                this.showNotification('Erreur lors du test des overlays', 'danger');
            }
        },

        refreshVmixStatus() {
            this.updateVmixStatus();
            this.loadVmixInputs();
            this.showNotification('Statut vMix rafraîchi', 'info');
        },

        // Chargement des équipes du match
        async loadMatchTeams() {
            try {
                const response = await fetch('/api/match/teams');
                if (response.ok) {
                    const teams = await response.json();
                    this.matchTeams = teams;
                } else {
                    this.showNotification('Erreur lors du chargement des équipes du match', 'warning');
                }
            } catch (error) {
                console.error('Erreur:', error);
                this.showNotification('Erreur de connexion au serveur', 'danger');
            }
        },

        // Notifications
        showNotification(message, type = 'info') {
            window.dispatchEvent(new CustomEvent('notification', {
                detail: { message, type }
            }));
        },

        // WebSocket
        setupWebSocket() {
            this.socket = io();

            this.socket.on('connect', () => {
                console.log('Connecté au WebSocket');
            });

            this.socket.on('vmix_status_update', (data) => {
                this.streamingStatus = data.streaming || false;
                this.recordingStatus = data.recording || false;
                this.showNotification('Statut vMix mis à jour', 'info');
            });

            this.socket.on('vmix_inputs_update', (data) => {
                this.vmixInputs = data.inputs || [];
                this.showNotification('Entrées vMix mises à jour', 'info');
            });

            this.socket.on('match_config_updated', () => {
                this.loadMatchTeams();
                this.showNotification('Configuration du match mise à jour', 'info');
            });
        }
    },
    mounted() {
        this.loadMatchTeams();
        this.setupWebSocket();

        // Charger la configuration sauvegardée
        fetch('/api/match/configuration')
            .then(response => response.json())
            .then(data => {
                if (data.vmixConfig) {
                    this.vmixHost = data.vmixConfig.host || '127.0.0.1';
                    this.vmixPort = data.vmixConfig.port || 8088;
                }

                if (data.matchInfo) {
                    this.matchInfo = { ...this.matchInfo, ...data.matchInfo };
                }

                if (data.overlayConfig) {
                    this.overlayConfig = { ...this.overlayConfig, ...data.overlayConfig };
                }

                if (data.thumbnailUrl) {
                    this.thumbnailPreview = data.thumbnailUrl;
                }

                // Tester la connexion vMix automatiquement
                this.checkVmixConnection();
            })
            .catch(error => {
                console.error('Erreur lors du chargement de la configuration:', error);
            });
    }
}).mount('#live-setup-app');
