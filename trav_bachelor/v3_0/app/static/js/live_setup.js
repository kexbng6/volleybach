// Application Vue pour la configuration du direct
const { createApp } = Vue;

createApp({
    data() {
        return {
            // Statut de connexion vMix
            vmixStatus: {
                connected: false,
                host: '127.0.0.1',
                port: 8088,
                lastChecked: null
            },

            // Configuration du streaming simplifiée
            streamingConfig: {
                title: '',
                rtmpUrl: '',
                streamKey: ''
            },

            // Contrôle de la miniature
            thumbnailVisible: false,
            thumbnailPreview: null,
            thumbnailFile: null,

            // Afficher/masquer la clé de stream
            showStreamKey: false
        }
    },

    mounted() {
        // Charger les configurations sauvegardées
        this.loadSavedConfig();

        // Vérifier la connexion à vMix au chargement
        this.checkVMixConnection();
    },

    methods: {
        // Formater une date pour l'affichage
        formatDateTime(timestamp) {
            if (!timestamp) return '';
            const date = new Date(timestamp);
            return date.toLocaleString();
        },

        // Vérifier la connexion à vMix
        checkVMixConnection() {
            fetch('/api/vmix/status')
                .then(response => response.json())
                .then(data => {
                    this.vmixStatus.connected = data.connected;
                    this.vmixStatus.lastChecked = new Date();

                    // Si des informations supplémentaires sont fournies par l'API
                    if (data.host) this.vmixStatus.host = data.host;
                    if (data.port) this.vmixStatus.port = data.port;
                })
                .catch(error => {
                    console.error('Erreur lors de la vérification de la connexion vMix:', error);
                    this.vmixStatus.connected = false;
                    this.vmixStatus.lastChecked = new Date();
                });
        },

        // Charger les configurations sauvegardées
        loadSavedConfig() {
            // Charger la configuration du streaming
            fetch('/api/stream/config')
                .then(response => response.json())
                .then(data => {
                    if (data.config) {
                        // Ne récupérer que les champs que nous utilisons
                        if (data.config.title) this.streamingConfig.title = data.config.title;
                        if (data.config.rtmpUrl) this.streamingConfig.rtmpUrl = data.config.rtmpUrl;
                        if (data.config.streamKey) this.streamingConfig.streamKey = data.config.streamKey;

                        // Charger la miniature si elle existe
                        if (data.config.thumbnailUrl) {
                            this.thumbnailPreview = data.config.thumbnailUrl;
                            this.thumbnailVisible = data.config.thumbnailVisible || false;
                        }
                    }
                })
                .catch(error => {
                    console.error('Erreur lors du chargement de la configuration de streaming:', error);
                });
        },

        // Enregistrer la configuration du streaming
        saveStreamingConfig() {
            const formData = new FormData();
            formData.append('title', this.streamingConfig.title);
            formData.append('rtmpUrl', this.streamingConfig.rtmpUrl);

            // N'envoyer la clé que si elle a été modifiée (pas les astérisques)
            if (this.streamingConfig.streamKey && !this.streamingConfig.streamKey.includes('•')) {
                formData.append('streamKey', this.streamingConfig.streamKey);
            }

            fetch('/api/stream/config', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                alert('Configuration RTMP enregistrée avec succès');
            })
            .catch(error => {
                console.error('Erreur lors de l\'enregistrement de la configuration:', error);
                alert('Erreur lors de l\'enregistrement de la configuration');
            });
        },

        // Gérer l'upload de la miniature
        handleThumbnailUpload(event) {
            const file = event.target.files[0];
            if (!file) return;

            this.thumbnailFile = file;

            // Créer une URL pour la prévisualisation
            this.thumbnailPreview = URL.createObjectURL(file);

            // Uploader la miniature automatiquement
            this.uploadThumbnail();
        },

        // Uploader la miniature au serveur
        uploadThumbnail() {
            if (!this.thumbnailFile) return;

            const formData = new FormData();
            formData.append('thumbnail', this.thumbnailFile);

            fetch('/api/stream/upload-thumbnail', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Mettre à jour l'URL de la miniature avec celle retournée par le serveur
                    this.thumbnailPreview = data.thumbnailUrl;
                    alert('Miniature téléchargée avec succès');
                } else {
                    alert('Erreur lors du téléchargement de la miniature: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Erreur lors du téléchargement de la miniature:', error);
                alert('Erreur lors du téléchargement de la miniature');
            });
        },

        // Supprimer la miniature
        removeThumbnail() {
            if (confirm('Êtes-vous sûr de vouloir supprimer cette miniature?')) {
                fetch('/api/stream/remove-thumbnail', {
                    method: 'POST'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        this.thumbnailPreview = null;
                        this.thumbnailFile = null;
                        alert('Miniature supprimée avec succès');
                    } else {
                        alert('Erreur lors de la suppression de la miniature: ' + data.message);
                    }
                })
                .catch(error => {
                    console.error('Erreur lors de la suppression de la miniature:', error);
                    alert('Erreur lors de la suppression de la miniature');
                });
            }
        },

        // Activer/désactiver la miniature dans vMix
        toggleThumbnail() {
            fetch('/api/stream/thumbnail/toggle', {  // Correction de l'URL pour correspondre au backend
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    show: this.thumbnailVisible
                })
            })
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    // Restaurer l'état précédent en cas d'erreur
                    this.thumbnailVisible = !this.thumbnailVisible;
                    alert('Erreur: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Erreur lors du changement de visibilité de la miniature:', error);
                // Restaurer l'état précédent en cas d'erreur
                this.thumbnailVisible = !this.thumbnailVisible;
                alert('Erreur de connexion au serveur');
            });
        }
    }
}).mount('#live-setup-app');
