// Application Vue pour la diffusion en direct
const { createApp } = Vue;

createApp({
    data() {
        return {
            // État de chargement
            loading: true,

            // Système de notifications
            notifications: [],
            notificationId: 0,

            // Données du score
            scoreData: {
                teamA: {
                    name: "Équipe A",
                    score: 0,
                    sets: 0
                },
                teamB: {
                    name: "Équipe B",
                    score: 0,
                    sets: 0
                }
            },

            // Statut de streaming et d'enregistrement
            streamingStatus: {
                isStreaming: false,
                isRecording: false,
                streamingStartTime: null,
                recordingStartTime: null,
                streamingTime: 0,
                recordingTime: 0
            },

            // Canal de streaming sélectionné
            streamingChannel: 0,

            // Configuration audio commentateur et ambiance
            commentatorAudio: true,
            commentatorVolume: 100,
            commentatorInputId: null,
            ambientAudio: true,
            ambientVolume: 80,
            ambientInputId: null,

            // Liste des entrées vidéo disponibles dans vMix
            videoInputs: [],

            // État de l'audio pour chaque entrée
            audioStates: {},

            // Configuration des replays
            replayConfig: {
                duration: 8
            },

            // État des replays
            replayStatus: {
                isRecording: false,
                isPlaying: false
            },

            // Événements de replay marqués
            replayEvents: [],

            // Nom pour le marquage d'événements
            eventName: "",

            // Canal actif pour le streaming
            activeStreamingChannel: null,

            // Statut du rafraîchissement
            isRefreshing: false,

            // Variables pour suivre les points consécutifs
            consecutivePoints: {
                A: 0,
                B: 0
            }
        };
    },

    computed: {
        // Afficher le bouton de rafraîchissement si aucune source audio n'est détectée
        showRefreshButton() {
            return !this.commentatorInputId && !this.ambientInputId;
        },

        // Calculer le nombre de points consécutifs pour l'équipe A
        consecutivePointsA() {
            return this.consecutivePoints.A || 0;
        },

        // Calculer le nombre de points consécutifs pour l'équipe B
        consecutivePointsB() {
            return this.consecutivePoints.B || 0;
        }
    },

    mounted() {
        // Initialiser l'application
        this.initialize();

        // Configurer socket.io pour les mises à jour en temps réel
        this.setupSocketConnection();

        // Mettre à jour les timers de streaming/enregistrement toutes les secondes
        setInterval(() => {
            this.updateTimers();
        }, 1000);
    },

    methods: {
        // Initialisation unifiée de l'application
        async initialize() {
            try {
                // Récupérer le statut de connexion à vMix
                await this.checkVMixConnection();

                // Récupérer les entrées vidéo disponibles
                await this.loadVMixInputs();

                // Charger les données des équipes du match
                await this.loadMatchTeams();

                // Vérifier l'état de streaming et d'enregistrement
                await this.checkStreamingStatus();

                // Charger les événements de replay existants
                await this.loadReplayEvents();

                // Détecter les inputs pour le commentateur et l'ambiance
                this.detectSpecialInputs();

                // Notification de démarrage
                this.addNotification("Interface de diffusion initialisée", "success");
            } catch (error) {
                console.error("Erreur lors de l'initialisation:", error);
                this.addNotification("Erreur lors de l'initialisation", "danger");
                this.loading = false;
            }
        },

        // Vérifier la connexion à vMix
        async checkVMixConnection() {
            try {
                const response = await fetch('/api/vmix/status');
                const data = await response.json();

                if (!data.connected) {
                    this.addNotification("Impossible de se connecter à vMix", "danger");
                    return false;
                }

                this.addNotification(`Connecté à vMix (${data.host}:${data.port})`, "success");
                return true;
            } catch (error) {
                console.error("Erreur lors de la vérification de la connexion vMix:", error);
                this.addNotification("Erreur lors de la connexion à vMix", "danger");
                return false;
            }
        },

        // Configuration de socket.io
        setupSocketConnection() {
            const socket = io();

            // Gérer les mises à jour de score
            socket.on('score_updated', (data) => {
                this.scoreData = data;
            });

            // Gérer les mises à jour de l'état de streaming
            socket.on('streaming_status', (data) => {
                this.updateStreamingStatus(data);
            });

            // Gérer les mises à jour des entrées vMix
            socket.on('vmix_inputs_updated', (data) => {
                this.videoInputs = data.inputs;
                this.initializeAudioStates();
            });

            // Gérer les notifications d'événements
            socket.on('event_notification', (data) => {
                this.addNotification(data.message, data.type || 'info');
            });

            // Gérer les mises à jour des événements de replay
            socket.on('replay_events_updated', (data) => {
                this.replayEvents = data.events;
            });
        },

        // Charger les entrées vMix
        async loadVMixInputs() {
            try {
                const response = await fetch('/api/vmix/inputs');
                const data = await response.json();

                // Organiser les inputs par catégorie
                this.videoInputs = data.video || [];

                // Trouver les sources audio principales
                // Chercher un input avec "commentateur" ou "comment" dans le nom pour le commentateur
                const commentatorInput = this.findInput(data.audio || [], 'comment');
                if (commentatorInput) {
                    this.commentatorInputId = commentatorInput.id;
                    console.log('Input commentateur trouvé:', commentatorInput.name);
                }

                // Chercher un input avec "ambiance" ou "ambient" dans le nom pour l'ambiance
                const ambientInput = this.findInput(data.audio || [], 'ambi');
                if (ambientInput) {
                    this.ambientInputId = ambientInput.id;
                    console.log('Input ambiance trouvé:', ambientInput.name);
                }

                // Ajouter les autres sources audio à videoInputs pour l'affichage
                if (data.audio) {
                    data.audio.forEach(input => {
                        if (!this.isSpecialAudioSource(input)) {
                            this.videoInputs.push(input);
                        }
                    });
                }

                this.initializeAudioStates();
                this.loadAudioStatus();
                this.loading = false;
            } catch (error) {
                console.error('Erreur lors du chargement des entrées vMix:', error);
                this.addNotification('Erreur lors du chargement des entrées vMix', 'danger');
                this.loading = false;
            }
        },

        // Trouver un input par mot-clé dans son nom
        findInput(inputs, keyword) {
            return inputs.find(input =>
                input.name && input.name.toLowerCase().includes(keyword.toLowerCase())
            );
        },

        // Vérifier si une source audio est spéciale (commentateur ou ambiance)
        isSpecialAudioSource(input) {
            if (!input || !input.id) return false;
            return input.id === this.commentatorInputId || input.id === this.ambientInputId;
        },

        // Initialiser l'état audio pour chaque entrée
        initializeAudioStates() {
            this.videoInputs.forEach(input => {
                if (this.audioStates[input.id] === undefined) {
                    this.audioStates[input.id] = true; // Audio activé par défaut
                }
            });
        },

        // Charger le statut audio des entrées vMix
        loadAudioStatus() {
            fetch('/api/vmix/audio/status')
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success' && data.audioStatus) {
                        // Mettre à jour les états audio selon les données reçues
                        const audioStatus = data.audioStatus;

                        for (const [inputId, status] of Object.entries(audioStatus)) {
                            this.audioStates[inputId] = !status.muted;

                            // Mettre à jour le volume du commentateur et de l'ambiance
                            if (inputId === this.commentatorInputId) {
                                this.commentatorVolume = parseInt(status.volume) || 100;
                                this.commentatorAudio = !status.muted;
                            } else if (inputId === this.ambientInputId) {
                                this.ambientVolume = parseInt(status.volume) || 80;
                                this.ambientAudio = !status.muted;
                            }
                        }
                    }
                })
                .catch(error => {
                    console.error('Erreur lors du chargement du statut audio:', error);
                });
        },

        // Activer/désactiver l'audio du commentateur
        toggleCommentatorAudio() {
            if (!this.commentatorInputId) return;

            fetch('/api/vmix/toggle-audio', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    inputId: this.commentatorInputId,
                    mute: !this.commentatorAudio
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    this.commentatorAudio = !this.commentatorAudio;
                    this.addNotification(`Audio commentateur ${this.commentatorAudio ? 'activé' : 'désactivé'}`, 'success');
                } else {
                    this.addNotification('Erreur lors de la modification de l\'audio commentateur', 'danger');
                }
            })
            .catch(error => {
                console.error('Erreur lors de la modification de l\'audio commentateur:', error);
                this.addNotification('Erreur lors de la modification de l\'audio commentateur', 'danger');
            });
        },

        // Mettre à jour le volume du commentateur
        updateCommentatorVolume() {
            if (!this.commentatorInputId) return;

            fetch('/api/vmix/audio/volume', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    inputId: this.commentatorInputId,
                    volume: this.commentatorVolume
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    this.addNotification(`Volume commentateur ajusté à ${this.commentatorVolume}%`, 'success');
                } else {
                    this.addNotification('Erreur lors de l\'ajustement du volume commentateur', 'danger');
                }
            })
            .catch(error => {
                console.error('Erreur lors de l\'ajustement du volume commentateur:', error);
                this.addNotification('Erreur lors de l\'ajustement du volume commentateur', 'danger');
            });
        },

        // Activer/désactiver l'audio d'ambiance
        toggleAmbientAudio() {
            if (!this.ambientInputId) return;

            fetch('/api/vmix/toggle-audio', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    inputId: this.ambientInputId,
                    mute: !this.ambientAudio
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    this.ambientAudio = !this.ambientAudio;
                    this.addNotification(`Audio d'ambiance ${this.ambientAudio ? 'activé' : 'désactivé'}`, 'success');
                } else {
                    this.addNotification('Erreur lors de la modification de l\'audio d\'ambiance', 'danger');
                }
            })
            .catch(error => {
                console.error('Erreur lors de la modification de l\'audio d\'ambiance:', error);
                this.addNotification('Erreur lors de la modification de l\'audio d\'ambiance', 'danger');
            });
        },

        // Mettre à jour le volume d'ambiance
        updateAmbientVolume() {
            if (!this.ambientInputId) return;

            fetch('/api/vmix/audio/volume', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    inputId: this.ambientInputId,
                    volume: this.ambientVolume
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    this.addNotification(`Volume d'ambiance ajusté à ${this.ambientVolume}%`, 'success');
                } else {
                    this.addNotification('Erreur lors de l\'ajustement du volume d\'ambiance', 'danger');
                }
            })
            .catch(error => {
                console.error('Erreur lors de l\'ajustement du volume d\'ambiance:', error);
                this.addNotification('Erreur lors de l\'ajustement du volume d\'ambiance', 'danger');
            });
        },

        // Activer/désactiver l'audio d'une entrée générique
        toggleAudio(inputId) {
            if (!inputId) return;

            fetch('/api/vmix/toggle-audio', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    inputId: inputId,
                    mute: !this.audioStates[inputId]
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Mettre à jour l'état audio localement
                    this.$set(this.audioStates, inputId, !this.audioStates[inputId]);
                    const inputName = this.getInputNameById(inputId);
                    this.addNotification(`Audio ${this.audioStates[inputId] ? 'activé' : 'désactivé'} pour ${inputName}`, 'success');
                } else {
                    this.addNotification('Erreur lors de la modification de l\'audio', 'danger');
                }
            })
            .catch(error => {
                console.error('Erreur lors de la modification de l\'audio:', error);
                this.addNotification('Erreur lors de la modification de l\'audio', 'danger');
            });
        },

        // Obtenir le nom d'un input par son ID
        getInputNameById(inputId) {
            const input = this.videoInputs.find(input => input.id === inputId);
            return input ? input.name : `Input ${inputId}`;
        },

        // Charger les données des équipes du match
        loadMatchTeams() {
            return fetch('/api/teams/match/current')
                .then(response => response.json())
                .then(data => {
                    if (data.team_a) {
                        this.scoreData.teamA.name = data.team_a.name;
                    }

                    if (data.team_b) {
                        this.scoreData.teamB.name = data.team_b.name;
                    }
                })
                .catch(error => {
                    console.error('Erreur lors du chargement des équipes du match:', error);
                });
        },

        // Vérifier l'état de streaming et d'enregistrement
        checkStreamingStatus() {
            return fetch('/api/vmix/streaming-status')
                .then(response => response.json())
                .then(data => {
                    this.updateStreamingStatus(data);
                })
                .catch(error => {
                    console.error('Erreur lors de la vérification du statut de streaming:', error);
                });
        },

        // Mettre à jour l'état de streaming et d'enregistrement
        updateStreamingStatus(data) {
            this.streamingStatus.isStreaming = data.isStreaming || false;
            this.streamingStatus.isRecording = data.isRecording || false;

            // Initialiser les timers si nécessaire
            if (this.streamingStatus.isStreaming && !this.streamingStatus.streamingStartTime) {
                this.streamingStatus.streamingStartTime = data.streamingStartTime || Date.now();
            } else if (!this.streamingStatus.isStreaming) {
                this.streamingStatus.streamingStartTime = null;
                this.streamingStatus.streamingTime = 0;
            }

            if (this.streamingStatus.isRecording && !this.streamingStatus.recordingStartTime) {
                this.streamingStatus.recordingStartTime = data.recordingStartTime || Date.now();
            } else if (!this.streamingStatus.isRecording) {
                this.streamingStatus.recordingStartTime = null;
                this.streamingStatus.recordingTime = 0;
            }
        },

        // Mettre à jour les timers de streaming et d'enregistrement
        updateTimers() {
            const now = Date.now();

            if (this.streamingStatus.isStreaming && this.streamingStatus.streamingStartTime) {
                this.streamingStatus.streamingTime = Math.floor((now - this.streamingStatus.streamingStartTime) / 1000);
            }

            if (this.streamingStatus.isRecording && this.streamingStatus.recordingStartTime) {
                this.streamingStatus.recordingTime = Math.floor((now - this.streamingStatus.recordingStartTime) / 1000);
            }
        },

        // Charger les événements de replay
        loadReplayEvents() {
            return fetch('/api/replay/events')
                .then(response => response.json())
                .then(data => {
                    this.replayEvents = data.events || [];
                    console.log("Événements de replay chargés:", this.replayEvents);
                })
                .catch(error => {
                    console.error('Erreur lors du chargement des événements de replay:', error);
                });
        },

        // Formater une durée en format mm:ss ou hh:mm:ss
        formatDuration(seconds) {
            if (!seconds) return '00:00';

            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            const remainingSeconds = seconds % 60;

            if (hours > 0) {
                return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
            } else {
                return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
            }
        },

        // Formater un timestamp en heure locale
        formatTime(timestamp) {
            if (!timestamp) return '';
            return new Date(timestamp).toLocaleTimeString();
        },

        // Ajouter une notification
        addNotification(message, type = 'info') {
            const id = this.notificationId++;
            this.notifications.push({ id, message, type });

            // Supprimer automatiquement après 5 secondes
            setTimeout(() => {
                this.notifications = this.notifications.filter(n => n.id !== id);
            }, 5000);
        },

        // Détecter les entrées spéciales (commentateur, ambiance)
        detectSpecialInputs() {
            // Chercher l'entrée du commentateur
            const commentatorInput = this.videoInputs.find(input =>
                input.name && (
                    input.name.toLowerCase().includes('comment') ||
                    input.name.toLowerCase().includes('micro') ||
                    input.name.toLowerCase().includes('mic')
                )
            );

            if (commentatorInput) {
                this.commentatorInputId = commentatorInput.id;
                console.log("Entrée commentateur détectée:", commentatorInput);
            }

            // Chercher l'entrée d'ambiance
            const ambientInput = this.videoInputs.find(input =>
                input.name && (
                    input.name.toLowerCase().includes('ambiance') ||
                    input.name.toLowerCase().includes('ambient') ||
                    input.name.toLowerCase().includes('crowd')
                )
            );

            if (ambientInput) {
                this.ambientInputId = ambientInput.id;
                console.log("Entrée ambiance détectée:", ambientInput);
            }
        },

        // === GESTION DU SCORE ===

        // Incrémenter le score d'une équipe
        incrementScore(team) {
            if (team === 'A') {
                this.scoreData.teamA.score++;
                // Incrémenter les points consécutifs pour l'équipe A
                this.consecutivePoints.A = (this.consecutivePoints.A || 0) + 1;
                // Réinitialiser les points consécutifs pour l'équipe B
                this.consecutivePoints.B = 0;
            } else {
                this.scoreData.teamB.score++;
                // Incrémenter les points consécutifs pour l'équipe B
                this.consecutivePoints.B = (this.consecutivePoints.B || 0) + 1;
                // Réinitialiser les points consécutifs pour l'équipe A
                this.consecutivePoints.A = 0;
            }
            this.updateScoreInVMix();
        },

        // Décrémenter le score d'une équipe
        decrementScore(team) {
            if (team === 'A' && this.scoreData.teamA.score > 0) {
                this.scoreData.teamA.score--;
                // Réinitialiser les points consécutifs
                this.consecutivePoints.A = 0;
            } else if (team === 'B' && this.scoreData.teamB.score > 0) {
                this.scoreData.teamB.score--;
                // Réinitialiser les points consécutifs
                this.consecutivePoints.B = 0;
            }
            this.updateScoreInVMix();
        },

        // Mettre à jour les sets
        updateSets(team) {
            if (team === 'A') {
                this.scoreData.teamA.sets++;
            } else {
                this.scoreData.teamB.sets++;
            }
            this.updateScoreInVMix();
        },

        // Réinitialiser les scores
        resetScores() {
            // Demander confirmation avant de réinitialiser
            if (confirm('Êtes-vous sûr de vouloir réinitialiser tous les scores?')) {
                // Réinitialiser les scores des deux équipes
                this.scoreData.teamA.score = 0;
                this.scoreData.teamB.score = 0;
                this.scoreData.teamA.sets = 0;
                this.scoreData.teamB.sets = 0;

                // Réinitialiser les points consécutifs
                this.consecutivePoints = { A: 0, B: 0 };

                // Mettre à jour le score dans vMix
                this.updateScoreInVMix();

                // Afficher une notification
                this.addNotification('Tous les scores ont été réinitialisés', 'success');
            }
        },

        // Commencer un nouveau set
        newSet() {
            // Demander confirmation avant de commencer un nouveau set
            if (confirm('Êtes-vous sûr de vouloir commencer un nouveau set?')) {
                // Déterminer le gagnant du set actuel
                if (this.scoreData.teamA.score > this.scoreData.teamB.score) {
                    // L'équipe A gagne le set
                    this.scoreData.teamA.sets++;
                } else if (this.scoreData.teamB.score > this.scoreData.teamA.score) {
                    // L'équipe B gagne le set
                    this.scoreData.teamB.sets++;
                } else {
                    // En cas d'égalité, demander qui gagne le set
                    if (confirm('Les scores sont à égalité. L\'équipe A remporte-t-elle le set? Cliquez sur Annuler pour l\'équipe B.')) {
                        this.scoreData.teamA.sets++;
                    } else {
                        this.scoreData.teamB.sets++;
                    }
                }

                // Réinitialiser les scores pour le nouveau set
                this.scoreData.teamA.score = 0;
                this.scoreData.teamB.score = 0;

                // Réinitialiser les points consécutifs
                this.consecutivePoints = { A: 0, B: 0 };

                // Mettre à jour le score dans vMix
                this.updateScoreInVMix();

                // Afficher une notification
                this.addNotification('Nouveau set commencé', 'success');
            }
        },

        // Envoyer le score vers vMix
        updateScoreInVMix() {
            fetch('/api/stream/update-score', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    teamA: {
                        name: this.scoreData.teamA.name,
                        score: this.scoreData.teamA.score,
                        sets: this.scoreData.teamA.sets
                    },
                    teamB: {
                        name: this.scoreData.teamB.name,
                        score: this.scoreData.teamB.score,
                        sets: this.scoreData.teamB.sets
                    }
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    this.addNotification('Score mis à jour dans vMix', 'success');
                } else {
                    this.addNotification('Erreur lors de la mise à jour du score', 'danger');
                }
            })
            .catch(error => {
                console.error('Erreur lors de la mise à jour du score:', error);
                this.addNotification('Erreur lors de la mise à jour du score', 'danger');
            });
        },

        // === GESTION DU STREAMING ===

        // Démarrer le streaming
        startStreaming() {
            // Récupérer le canal sélectionné et ajouter 1 pour la correspondance avec vMix (canaux 1-5)
            const selectedChannel = parseInt(this.streamingChannel) + 1;

            fetch('/api/vmix/start-streaming', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    channel: selectedChannel
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    this.addNotification(data.error, 'danger');
                } else {
                    // Enregistrer le canal utilisé pour pouvoir l'utiliser lors de l'arrêt
                    this.activeStreamingChannel = selectedChannel;
                    this.addNotification(`Streaming démarré sur le canal ${selectedChannel}`, 'success');
                    this.streamingStatus.isStreaming = true;
                    this.streamingStatus.streamingStartTime = Date.now();
                }
            })
            .catch(error => {
                console.error('Erreur lors du démarrage du streaming:', error);
                this.addNotification('Erreur lors du démarrage du streaming', 'danger');
            });
        },

        // Arrêter le streaming
        stopStreaming() {
            if (confirm('Êtes-vous sûr de vouloir arrêter le streaming?')) {
                // Utiliser le canal actif pour l'arrêt du streaming
                const channelToStop = this.activeStreamingChannel || parseInt(this.streamingChannel) + 1;

                fetch('/api/vmix/stop-streaming', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        channel: channelToStop
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        this.addNotification(data.error, 'danger');
                    } else {
                        this.addNotification('Streaming arrêté', 'success');
                        this.streamingStatus.isStreaming = false;
                        this.streamingStatus.streamingStartTime = null;
                        this.streamingStatus.streamingTime = 0;
                    }
                })
                .catch(error => {
                    console.error('Erreur lors de l\'arrêt du streaming:', error);
                    this.addNotification('Erreur lors de l\'arrêt du streaming', 'danger');
                });
            }
        },

        // Démarrer l'enregistrement
        startRecording() {
            fetch('/api/vmix/start-recording', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    this.addNotification(data.error, 'danger');
                } else {
                    this.addNotification('Enregistrement démarré', 'success');
                    this.streamingStatus.isRecording = true;
                    this.streamingStatus.recordingStartTime = Date.now();
                }
            })
            .catch(error => {
                console.error('Erreur lors du démarrage de l\'enregistrement:', error);
                this.addNotification('Erreur lors du démarrage de l\'enregistrement', 'danger');
            });
        },

        // Arrêter l'enregistrement
        stopRecording() {
            if (confirm('Êtes-vous sûr de vouloir arrêter l\'enregistrement?')) {
                fetch('/api/vmix/stop-recording', {
                    method: 'POST'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        this.addNotification(data.error, 'danger');
                    } else {
                        this.addNotification('Enregistrement arrêté', 'success');
                        this.streamingStatus.isRecording = false;
                        this.streamingStatus.recordingStartTime = null;
                        this.streamingStatus.recordingTime = 0;
                    }
                })
                .catch(error => {
                    console.error('Erreur lors de l\'arrêt de l\'enregistrement:', error);
                    this.addNotification('Erreur lors de l\'arrêt de l\'enregistrement', 'danger');
                });
            }
        },

        // === GESTION DES CAMÉRAS ===

        // Changer d'entrée vidéo
        switchToInput(inputId, transitionType = 'cut') {
            fetch('/api/vmix/switch-input', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    inputId: inputId,
                    transitionType: transitionType
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    this.addNotification(data.error, 'danger');
                } else {
                    const inputName = this.videoInputs.find(input => input.id === inputId)?.name || inputId;
                    this.addNotification(`Passage à ${inputName} (${transitionType})`, 'success');
                }
            })
            .catch(error => {
                console.error('Erreur lors du changement d\'entrée:', error);
                this.addNotification('Erreur lors du changement d\'entrée', 'danger');
            });
        },

        // Rafraîchir les entrées audio
        refreshAudioInputs() {
            this.isRefreshing = true;

            fetch('/api/vmix/inputs')
                .then(response => response.json())
                .then(data => {
                    // Mettre à jour les entrées vidéo
                    this.videoInputs = data.video || [];

                    // Réinitialiser les IDs des sources spéciales
                    this.commentatorInputId = null;
                    this.ambientInputId = null;

                    // Chercher les sources audio spéciales dans les entrées audio
                    if (data.audio) {
                        data.audio.forEach(input => {
                            const inputName = input.name.toLowerCase();

                            // Détecter le commentateur
                            if (!this.commentatorInputId && (
                                inputName.includes('comment') ||
                                inputName.includes('micro') ||
                                inputName.includes('mic')
                            )) {
                                this.commentatorInputId = input.id;
                                console.log('Input commentateur trouvé:', input.name);
                            }

                            // Détecter l'ambiance
                            if (!this.ambientInputId && (
                                inputName.includes('ambiance') ||
                                inputName.includes('ambient') ||
                                inputName.includes('room')
                            )) {
                                this.ambientInputId = input.id;
                                console.log('Input ambiance trouvé:', input.name);
                            }

                            // Ajouter à la liste des entrées si ce n'est pas une source spéciale
                            if (!this.isSpecialAudioSource(input)) {
                                this.videoInputs.push(input);
                            }
                        });
                    }

                    // Initialiser les états audio et charger leur statut
                    this.initializeAudioStates();
                    this.loadAudioStatus();

                    // Afficher un message approprié
                    if (this.commentatorInputId || this.ambientInputId) {
                        this.addNotification('Sources audio détectées et mises à jour', 'success');
                    } else {
                        this.addNotification('Aucune source audio spéciale trouvée', 'warning');
                    }
                })
                .catch(error => {
                    console.error('Erreur lors du rafraîchissement des entrées audio:', error);
                    this.addNotification('Erreur lors du rafraîchissement des entrées audio', 'danger');
                })
                .finally(() => {
                    this.isRefreshing = false;
                });
        },

        // === GESTION DES REPLAYS ===

        // Définir la durée du buffer de replay
        setReplayDuration() {
            fetch('/api/replay/set-duration', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    duration: this.replayConfig.duration
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    this.addNotification(data.message || 'Durée du buffer définie avec succès', 'success');
                } else {
                    this.addNotification(data.error || 'Erreur lors de la définition de la durée du buffer', 'danger');
                }
            })
            .catch(error => {
                console.error('Erreur lors de la définition de la durée du replay:', error);
                this.addNotification('Erreur lors de la définition de la durée du replay', 'danger');
            });
        },

        // Activer/désactiver l'enregistrement des replays
        toggleReplayRecording() {
            const action = this.replayStatus.isRecording ? 'stop-recording' : 'start-recording';

            fetch(`/api/replay/${action}`, {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    this.replayStatus.isRecording = !this.replayStatus.isRecording;
                    const actionText = this.replayStatus.isRecording ? 'démarré' : 'arrêté';
                    this.addNotification(`Enregistrement des replays ${actionText}`, 'success');
                } else {
                    this.addNotification(data.error || `Erreur lors de l'action sur l'enregistrement des replays`, 'danger');
                }
            })
            .catch(error => {
                console.error('Erreur lors de la gestion de l\'enregistrement des replays:', error);
                this.addNotification('Erreur lors de la gestion de l\'enregistrement des replays', 'danger');
            });
        },

        // Lire le dernier replay
        playLastReplay(speed) {
            fetch('/api/replay/play-last', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    speed: speed
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    this.addNotification(`Lecture du dernier replay à ${speed}%`, 'success');
                } else {
                    this.addNotification(data.error || 'Erreur lors de la lecture du replay', 'danger');
                }
            })
            .catch(error => {
                console.error('Erreur lors de la lecture du replay:', error);
                this.addNotification('Erreur lors de la lecture du replay', 'danger');
            });
        },

        // Mettre en pause le replay
        pauseReplay() {
            fetch('/api/replay/pause', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    this.addNotification('Replay mis en pause', 'success');
                } else {
                    this.addNotification(data.error || 'Erreur lors de la mise en pause du replay', 'danger');
                }
            })
            .catch(error => {
                console.error('Erreur lors de la mise en pause du replay:', error);
                this.addNotification('Erreur lors de la mise en pause du replay', 'danger');
            });
        },

        // Marquer un événement de replay
        markReplayEvent(eventName) {
            // Si eventName est un objet d'événement DOM ou n'est pas une chaîne, utiliser this.eventName à la place
            const actualEventName = (typeof eventName === 'string') ? eventName : this.eventName;

            // Si aucun nom n'est fourni, utiliser un nom par défaut
            const eventDisplayName = actualEventName || `Événement ${this.replayEvents.length + 1}`;

            fetch('/api/replay/mark', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: eventDisplayName,
                    type: 'custom'
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Mettre à jour la liste des événements si elle est retournée par l'API
                    if (data.events && Array.isArray(data.events)) {
                        this.replayEvents = data.events;
                    } else {
                        // Sinon, recharger les événements
                        this.loadReplayEvents();
                    }

                    // Réinitialiser le champ de saisie
                    this.eventName = '';

                    // Afficher une notification de succès
                    this.addNotification(`Événement "${eventDisplayName}" marqué avec succès`, 'success');
                } else {
                    // Afficher l'erreur retournée par l'API
                    this.addNotification(data.error || 'Erreur lors du marquage de l\'événement', 'danger');
                }
            })
            .catch(error => {
                console.error('Erreur lors du marquage de l\'événement:', error);
                this.addNotification('Erreur lors du marquage de l\'événement', 'danger');
            });
        },

        // Lire un événement de replay spécifique
        playReplayEvent(eventIndex, speed) {
            fetch('/api/replay/play-event', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    eventIndex: eventIndex,
                    speed: speed
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    this.addNotification(`Lecture de l'événement à ${speed}%`, 'success');
                } else {
                    this.addNotification(data.error || 'Erreur lors de la lecture de l\'événement', 'danger');
                }
            })
            .catch(error => {
                console.error('Erreur lors de la lecture de l\'événement:', error);
                this.addNotification('Erreur lors de la lecture de l\'événement', 'danger');
            });
        },

        // Supprimer un événement de replay
        deleteReplayEvent(eventIndex) {
            if (confirm('Êtes-vous sûr de vouloir supprimer cet événement ?')) {
                fetch('/api/replay/delete-event', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        eventIndex: eventIndex
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        this.addNotification('Événement supprimé avec succès', 'success');
                        // Recharger les événements de replay après suppression
                        this.loadReplayEvents();
                    } else {
                        this.addNotification(data.error || 'Erreur lors de la suppression de l\'événement', 'danger');
                    }
                })
                .catch(error => {
                    console.error('Erreur lors de la suppression de l\'événement:', error);
                    this.addNotification('Erreur lors de la suppression de l\'événement', 'danger');
                });
            }
        }
    }
}).mount('#live-broadcast-app');
