// Module pour gérer la diffusion en direct
const { createApp } = Vue;

createApp({
    delimiters: ['[[', ']]'], // Pour éviter les conflits avec Jinja
    data() {
        return {
            inputs: [],
            loading: true,
            audioStates: {}, // true = unmute, false = mute
            audioVolumes: {},
            transitionDuration: 500,
            transitionEffect: 'Fade',
            notifications: [],
            notificationCounter: 0,
            
            // Données pour les replays
            replayDuration: 8,
            isRecordingReplay: false,
            eventName: '',
            replayEvents: [],
            lastEventIndex: 0,

            // Données pour le score de volleyball
            scoreTeamA: 0,
            scoreTeamB: 0,
            setsTeamA: 0,
            setsTeamB: 0,

            // Compteurs de points sans ralenti
            consecutivePointsA: 0,
            consecutivePointsB: 0,
            totalPointsSinceReplay: 0, // Compteur total des points depuis le dernier replay
            lastReplayTimestamp: Date.now(),

            // Noms des équipes (à récupérer ultérieurement depuis la config)
            teamAName: 'Équipe A',
            teamBName: 'Équipe B',

            // ID du titre vMix pour le scoreboard
            scoreboardTitleId: null
        };
    },
    computed: {
        cameraInputs() {
            return this.inputs.filter(input => input.category === 'camera');
        },
        videoInputs() {
            return this.inputs.filter(input => input.category === 'video');
        },
        audioInputs() {
            return this.inputs.filter(input => input.category === 'audio');
        }
    },
    methods: {
        // Système de notifications
        showNotification(message, type = 'info', duration = 5000) {
            const id = this.notificationCounter++;
            this.notifications.push({ id, message, type });

            // Auto-supprimer après la durée spécifiée
            setTimeout(() => {
                this.notifications = this.notifications.filter(n => n.id !== id);
            }, duration);
        },

        // Chargement des inputs vMix
        async loadInputs() {
            this.loading = true;
            try {
                // Utiliser l'API existante de vmix_manager au lieu de créer un endpoint dupliqué
                const response = await fetch('/api/vmix/inputs');
                const data = await response.json();

                if (data.success) {
                    this.inputs = data.inputs;

                    // Initialiser les états audio pour toutes les entrées
                    this.inputs.forEach(input => {
                        // Si nous n'avons pas encore d'état pour cet input, initialiser à true (non muet)
                        if (this.audioStates[input.id] === undefined) {
                            this.audioStates[input.id] = true;
                        }

                        // Si nous n'avons pas encore de volume pour cet input, initialiser à 100%
                        if (this.audioVolumes[input.id] === undefined) {
                            this.audioVolumes[input.id] = 100;
                        }

                        // Chercher l'ID du titre vMix pour le scoreboard
                        if (input.type === 'GT' && input.name && input.name.toLowerCase().includes('scoreboard')) {
                            this.scoreboardTitleId = input.id;
                        }
                    });

                    this.showNotification('Sources vMix chargées avec succès', 'success');
                } else {
                    this.showNotification('Erreur lors du chargement des inputs : ' + (data.error || "Erreur inconnue"), 'danger');
                }
            } catch (e) {
                this.showNotification('Erreur de communication avec le serveur : ' + e.message, 'danger');
            } finally {
                this.loading = false;
            }
        },

        // Gestion des caméras
        async cutToCamera(inputId) {
            try {
                const response = await fetch('/api/broadcast/camera/cut', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        input: inputId
                    })
                });

                const data = await response.json();
                if (data.success) {
                    // Trouver le nom de la caméra pour l'afficher dans la notification
                    const inputName = this.inputs.find(input => input.id === inputId)?.name || inputId;
                    this.showNotification(`Changement vers ${inputName} effectué (CUT)`, 'success');
                } else {
                    this.showNotification(`Erreur lors du changement de caméra : ${data.error || "Erreur inconnue"}`, 'danger');
                }
            } catch (e) {
                this.showNotification(`Erreur de communication avec le serveur : ${e.message}`, 'danger');
            }
        },

        async transitionToCamera(inputId) {
            try {
                const response = await fetch('/api/broadcast/camera/transition', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        input: inputId,
                        duration: this.transitionDuration,
                        effect: this.transitionEffect
                    })
                });

                const data = await response.json();
                if (data.success) {
                    // Trouver le nom de la caméra pour l'afficher dans la notification
                    const inputName = this.inputs.find(input => input.id === inputId)?.name || inputId;
                    this.showNotification(`Transition vers ${inputName} effectuée`, 'success');
                } else {
                    this.showNotification(`Erreur lors de la transition : ${data.error || "Erreur inconnue"}`, 'danger');
                }
            } catch (e) {
                this.showNotification(`Erreur de communication avec le serveur : ${e.message}`, 'danger');
            }
        },

        // Gestion audio
        async toggleAudio(inputId) {
            try {
                const currentState = this.audioStates[inputId];

                const response = await fetch('/api/broadcast/audio/toggle', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        input: inputId,
                        mute: currentState // Si true (unmuted), on demande de muter
                    })
                });

                const data = await response.json();
                if (data.success) {
                    // Inverser l'état audio localement
                    this.audioStates[inputId] = !currentState;

                    // Trouver le nom de la source pour l'afficher dans la notification
                    const inputName = this.inputs.find(input => input.id === inputId)?.name || inputId;
                    const statusText = this.audioStates[inputId] ? 'activé' : 'désactivé';
                    this.showNotification(`Audio ${statusText} pour ${inputName}`, 'success');
                } else {
                    this.showNotification(`Erreur lors du changement d'état audio : ${data.error || "Erreur inconnue"}`, 'danger');
                }
            } catch (e) {
                this.showNotification(`Erreur de communication avec le serveur : ${e.message}`, 'danger');
            }
        },

        async adjustVolume(inputId) {
            const volume = this.audioVolumes[inputId];
            try {
                const response = await fetch('/api/broadcast/audio/volume', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        input: inputId,
                        volume: volume
                    })
                });

                const data = await response.json();
                if (data.success) {
                    // Trouver le nom de la source pour l'afficher dans la notification
                    const inputName = this.inputs.find(input => input.id === inputId)?.name || inputId;
                    this.showNotification(`Volume réglé à ${volume}% pour ${inputName}`, 'info');
                } else {
                    this.showNotification(`Erreur lors de l'ajustement du volume : ${data.error || "Erreur inconnue"}`, 'danger');
                }
            } catch (e) {
                this.showNotification(`Erreur de communication avec le serveur : ${e.message}`, 'danger');
            }
        },

        // Contrôle du streaming
        async startStreaming() {
            try {
                const response = await fetch('/api/broadcast/streaming', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        action: 'Start'
                    })
                });

                const data = await response.json();
                if (data.success) {
                    this.showNotification('Streaming démarré avec succès', 'success');
                } else {
                    this.showNotification(`Erreur lors du démarrage du streaming : ${data.error || "Erreur inconnue"}`, 'danger');
                }
            } catch (e) {
                this.showNotification(`Erreur de communication avec le serveur : ${e.message}`, 'danger');
            }
        },

        async stopStreaming() {
            try {
                const response = await fetch('/api/broadcast/streaming', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        action: 'Stop'
                    })
                });

                const data = await response.json();
                if (data.success) {
                    this.showNotification('Streaming arrêté avec succès', 'warning');
                } else {
                    this.showNotification(`Erreur lors de l'arrêt du streaming : ${data.error || "Erreur inconnue"}`, 'danger');
                }
            } catch (e) {
                this.showNotification(`Erreur de communication avec le serveur : ${e.message}`, 'danger');
            }
        },

        // Gestion des replays
        async setReplayDuration() {
            try {
                const response = await fetch('/api/broadcast/replay/duration', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        duration: this.replayDuration
                    })
                });

                const data = await response.json();
                if (data.success) {
                    this.showNotification(`Durée du buffer de replay définie à ${this.replayDuration} secondes`, 'success');
                } else {
                    this.showNotification(`Erreur lors de la définition de la durée du replay : ${data.error || "Erreur inconnue"}`, 'danger');
                }
            } catch (e) {
                this.showNotification(`Erreur de communication avec le serveur : ${e.message}`, 'danger');
            }
        },

        async startReplayRecording() {
            if (this.isRecordingReplay) {
                this.showNotification('Un replay est déjà en cours d\'enregistrement', 'warning');
                return;
            }

            this.isRecordingReplay = true;

            // Démarrer l'enregistrement du replay
            try {
                const response = await fetch('/api/broadcast/replay/start', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        duration: this.replayDuration
                    })
                });

                const data = await response.json();
                if (data.success) {
                    this.showNotification(`Enregistrement du replay démarré (Durée : ${this.replayDuration}s)`, 'success');
                } else {
                    this.isRecordingReplay = false;
                    this.showNotification(`Erreur lors du démarrage de l'enregistrement du replay : ${data.error || "Erreur inconnue"}`, 'danger');
                }
            } catch (e) {
                this.isRecordingReplay = false;
                this.showNotification(`Erreur de communication avec le serveur : ${e.message}`, 'danger');
            }
        },

        async stopReplayRecording() {
            if (!this.isRecordingReplay) {
                this.showNotification('Aucun replay n\'est en cours d\'enregistrement', 'warning');
                return;
            }

            // Arrêter l'enregistrement du replay
            try {
                const response = await fetch('/api/broadcast/replay/stop', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                const data = await response.json();
                if (data.success) {
                    this.isRecordingReplay = false;
                    this.showNotification('Enregistrement du replay arrêté avec succès', 'success');

                    // Réinitialiser le nom de l'événement
                    this.eventName = '';
                } else {
                    this.showNotification(`Erreur lors de l'arrêt de l'enregistrement du replay : ${data.error || "Erreur inconnue"}`, 'danger');
                }
            } catch (e) {
                this.showNotification(`Erreur de communication avec le serveur : ${e.message}`, 'danger');
            }
        },

        async markReplayEvent() {
            if (!this.isRecordingReplay) {
                this.showNotification('Aucun replay n\'est en cours d\'enregistrement. Impossible de marquer un événement.', 'warning');
                return;
            }

            try {
                const eventData = {
                    name: this.eventName || `Événement ${this.replayEvents.length + 1}`,
                    timestamp: Date.now(),
                    // Ajouter la durée du buffer comme référence
                    duration: this.replayDuration
                };

                const response = await fetch('/api/broadcast/replay/mark', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(eventData)
                });

                const data = await response.json();
                if (data.success) {
                    // Ajout de l'index vMix au marquage pour le retrouver plus facilement
                    eventData.vmixIndex = data.eventIndex || 0;
                    this.replayEvents.push(eventData);
                    this.showNotification(`Événement "${eventData.name}" marqué avec succès`, 'success');
                    this.eventName = ''; // Réinitialiser le nom après marquage
                } else {
                    this.showNotification(`Erreur lors du marquage de l'événement : ${data.error || "Erreur inconnue"}`, 'danger');
                }
            } catch (e) {
                this.showNotification(`Erreur de communication avec le serveur : ${e.message}`, 'danger');
            }
        },

        async playLastReplay(speed) {
            if (this.replayEvents.length === 0) {
                this.showNotification('Aucun événement de replay disponible', 'warning');
                return;
            }

            const lastEvent = this.replayEvents[this.replayEvents.length - 1];
            await this.playReplayEvent(this.replayEvents.length - 1, speed);

            // Réinitialiser les compteurs lorsqu'un replay est joué
            this.resetConsecutivePointsOnReplay();
        },

        async playReplayEvent(index, speed) {
            const event = this.replayEvents[index];
            if (!event) {
                this.showNotification('Événement de replay non trouvé', 'danger');
                return;
            }

            try {
                const response = await fetch('/api/broadcast/replay/play', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        timestamp: event.timestamp,
                        speed: speed
                    })
                });

                const data = await response.json();
                if (data.success) {
                    this.showNotification(`Lecture du replay "${event.name}" à ${speed}%`, 'success');

                    // Réinitialiser les compteurs lorsqu'un replay est joué
                    this.resetConsecutivePointsOnReplay();
                } else {
                    this.showNotification(`Erreur lors de la lecture du replay : ${data.error || "Erreur inconnue"}`, 'danger');
                }
            } catch (e) {
                this.showNotification(`Erreur de communication avec le serveur : ${e.message}`, 'danger');
            }
        },

        async pauseReplay() {
            try {
                const response = await fetch('/api/broadcast/replay/pause', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                const data = await response.json();
                if (data.success) {
                    this.showNotification('Replay mis en pause', 'info');
                } else {
                    this.showNotification(`Erreur lors de la mise en pause du replay : ${data.error || "Erreur inconnue"}`, 'danger');
                }
            } catch (e) {
                this.showNotification(`Erreur de communication avec le serveur : ${e.message}`, 'danger');
            }
        },

        // Chargement des événements de replay
        async loadReplays() {
            try {
                const response = await fetch('/api/broadcast/replays');
                const data = await response.json();

                if (data.success) {
                    this.replayEvents = data.replays;
                } else {
                    this.showNotification('Erreur lors du chargement des replays : ' + (data.error || "Erreur inconnue"), 'danger');
                }
            } catch (e) {
                this.showNotification('Erreur de communication avec le serveur : ' + e.message, 'danger');
            }
        },

        // Suppression d'un événement de replay
        async deleteReplay(event) {
            try {
                const response = await fetch('/api/broadcast/replay/delete', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        timestamp: event.timestamp
                    })
                });

                const data = await response.json();
                if (data.success) {
                    this.showNotification(`Replay "${event.name}" supprimé`, 'success');

                    // Mettre à jour la liste des événements de replay
                    this.replayEvents = this.replayEvents.filter(e => e.timestamp !== event.timestamp);
                } else {
                    this.showNotification(`Erreur lors de la suppression du replay : ${data.error || "Erreur inconnue"}`, 'danger');
                }
            } catch (e) {
                this.showNotification(`Erreur de communication avec le serveur : ${e.message}`, 'danger');
            }
        },

        // Nouvelles méthodes pour la gestion du score

        // Ajouter un point à l'équipe A
        addPointTeamA() {
            this.scoreTeamA++;
            this.consecutivePointsA++;
            this.consecutivePointsB = 0; // Réinitialiser le compteur de l'équipe adverse
            this.totalPointsSinceReplay++; // Incrémenter le compteur total

            // Vérifier si le set est terminé (en volleyball, un set se termine généralement à 25 points avec 2 points d'écart)
            if (this.scoreTeamA >= 25 && this.scoreTeamA - this.scoreTeamB >= 2) {
                this.setsTeamA++;
                this.showNotification(`L'équipe A remporte le set: ${this.scoreTeamA}-${this.scoreTeamB}`, 'success');
                this.resetSetScores();
            }

            // Mettre à jour le score dans vMix
            this.updateScoreInVMix();

            // Marquer automatiquement un point pour un éventuel ralenti
            this.markPointForReplay(`Point équipe A (${this.scoreTeamA}-${this.scoreTeamB})`);
        },

        // Retirer un point à l'équipe A (correction)
        removePointTeamA() {
            if (this.scoreTeamA > 0) {
                this.scoreTeamA--;
                this.consecutivePointsA = Math.max(0, this.consecutivePointsA - 1);
                this.updateScoreInVMix();
            }
        },

        // Ajouter un point à l'équipe B
        addPointTeamB() {
            this.scoreTeamB++;
            this.consecutivePointsB++;
            this.consecutivePointsA = 0; // Réinitialiser le compteur de l'équipe adverse
            this.totalPointsSinceReplay++; // Incrémenter le compteur total

            // Vérifier si le set est terminé
            if (this.scoreTeamB >= 25 && this.scoreTeamB - this.scoreTeamA >= 2) {
                this.setsTeamB++;
                this.showNotification(`L'équipe B remporte le set: ${this.scoreTeamB}-${this.scoreTeamA}`, 'success');
                this.resetSetScores();
            }

            // Mettre à jour le score dans vMix
            this.updateScoreInVMix();

            // Marquer automatiquement un point pour un éventuel ralenti
            this.markPointForReplay(`Point équipe B (${this.scoreTeamB}-${this.scoreTeamA})`);
        },

        // Retirer un point à l'équipe B (correction)
        removePointTeamB() {
            if (this.scoreTeamB > 0) {
                this.scoreTeamB--;
                this.consecutivePointsB = Math.max(0, this.consecutivePointsB - 1);
                this.updateScoreInVMix();
            }
        },

        // Réinitialiser les scores pour un nouveau set
        resetSetScores() {
            this.scoreTeamA = 0;
            this.scoreTeamB = 0;
            this.consecutivePointsA = 0;
            this.consecutivePointsB = 0;
        },

        // Mettre à jour le score dans vMix
        async updateScoreInVMix() {
            // Vérifier si nous avons trouvé un titre de scoreboard
            if (!this.scoreboardTitleId) {
                this.showNotification("Impossible de trouver le titre scoreboard dans vMix", 'warning');
                return;
            }

            try {
                const response = await fetch('/api/vmix/update-title', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        inputId: this.scoreboardTitleId,
                        values: {
                            TeamAName: this.teamAName,
                            TeamBName: this.teamBName,
                            ScoreA: this.scoreTeamA.toString(),
                            ScoreB: this.scoreTeamB.toString(),
                            SetsA: this.setsTeamA.toString(),
                            SetsB: this.setsTeamB.toString()
                        }
                    })
                });

                const data = await response.json();
                if (data.success) {
                    this.showNotification("Score mis à jour dans vMix", 'success', 1500);
                } else {
                    this.showNotification(`Erreur lors de la mise à jour du score: ${data.error || "Erreur inconnue"}`, 'danger');
                }
            } catch (e) {
                this.showNotification(`Erreur de communication avec le serveur: ${e.message}`, 'danger');
            }
        },

        // Suggérer un replay pour l'équipe A après 3+ points consécutifs
        suggestReplayForTeamA() {
            // Mettre en pause l'enregistrement actuel si nécessaire
            if (this.isRecordingReplay) {
                this.stopReplayRecording();
            }

            // Définir le nom de l'événement pour le replay
            this.eventName = `Série de ${this.consecutivePointsA} points - Équipe A`;

            // Démarrer l'enregistrement pour le prochain point
            this.startReplayRecording();

            // Afficher une notification pour confirmer l'action
            this.showNotification(`Enregistrement lancé pour la série de points de l'équipe A`, 'info');

            // Réinitialiser le compteur après avoir suggéré un replay
            this.consecutivePointsA = 0;
        },

        // Suggérer un replay pour l'équipe B après 3+ points consécutifs
        suggestReplayForTeamB() {
            // Mettre en pause l'enregistrement actuel si nécessaire
            if (this.isRecordingReplay) {
                this.stopReplayRecording();
            }

            // Définir le nom de l'événement pour le replay
            this.eventName = `Série de ${this.consecutivePointsB} points - Équipe B`;

            // Démarrer l'enregistrement pour le prochain point
            this.startReplayRecording();

            // Afficher une notification pour confirmer l'action
            this.showNotification(`Enregistrement lancé pour la série de points de l'équipe B`, 'info');

            // Réinitialiser le compteur après avoir suggéré un replay
            this.consecutivePointsB = 0;
        },

        // Réinitialiser les compteurs de points consécutifs lorsqu'un replay est joué
        resetConsecutivePointsOnReplay() {
            this.consecutivePointsA = 0;
            this.consecutivePointsB = 0;
            this.totalPointsSinceReplay = 0; // Réinitialiser le compteur total
            this.lastReplayTimestamp = Date.now();
        },

        // Suggérer un replay basé sur le nombre total de points marqués
        suggestReplayForTotalPoints() {
            // Mettre en pause l'enregistrement actuel si nécessaire
            if (this.isRecordingReplay) {
                this.stopReplayRecording();
            }

            // Définir le nom de l'événement pour le replay
            this.eventName = `Dernier(s) ${this.totalPointsSinceReplay} point(s) - Score: ${this.scoreTeamA}-${this.scoreTeamB}`;

            // Démarrer l'enregistrement pour le prochain point
            this.startReplayRecording();

            // Afficher une notification pour confirmer l'action
            this.showNotification(`Enregistrement lancé pour les derniers points`, 'info');

            // Réinitialiser le compteur total après avoir suggéré un replay
            this.totalPointsSinceReplay = 0;
        },
        // Créer une popup de confirmation pour suggérer un replay
        showReplaySuggestion(team, points) {
            // Créer une notification persistante (durée plus longue)
            const message = `${team} a marqué ${points} points sans ralenti. Lancer un replay?`;
            const id = this.notificationCounter++;

            // Créer un élément DOM pour la notification spéciale
            const notifElement = document.createElement('div');
            notifElement.className = 'toast show text-bg-warning';
            notifElement.style.zIndex = '1060';

            notifElement.innerHTML = `
                <div class="toast-header">
                    <strong class="me-auto">Suggestion de Replay</strong>
                    <button type="button" class="btn-close" aria-label="Close"></button>
                </div>
                <div class="toast-body">
                    <p>${message}</p>
                    <div class="mt-2 pt-2 border-top">
                        <button type="button" class="btn btn-primary btn-sm" id="accept-replay">
                            <i class="bi bi-camera-reels me-1"></i> Lancer un replay
                        </button>
                        <button type="button" class="btn btn-secondary btn-sm" id="reject-replay">
                            Ignorer
                        </button>
                    </div>
                </div>
            `;

            // Ajouter la notification à la page
            const notifContainer = document.querySelector('.position-fixed.top-0.end-0.p-3');
            notifContainer.appendChild(notifElement);

            // Gérer les boutons de la notification
            notifElement.querySelector('#accept-replay').addEventListener('click', () => {
                if (team === 'Équipe A') {
                    this.suggestReplayForTeamA();
                } else {
                    this.suggestReplayForTeamB();
                }
                notifContainer.removeChild(notifElement);
            });

            notifElement.querySelector('#reject-replay, .btn-close').addEventListener('click', () => {
                notifContainer.removeChild(notifElement);
            });

            // Auto-supprimer après 15 secondes
            setTimeout(() => {
                if (notifElement.parentNode === notifContainer) {
                    notifContainer.removeChild(notifElement);
                }
            }, 15000);
        },

        // Créer une popup de confirmation pour suggérer un replay basé sur le nombre total de points
        showTotalPointsReplaySuggestion(totalPoints) {
            // Créer une notification persistante (durée plus longue)
            const message = `${totalPoints} points ont été marqués depuis le dernier ralenti.`;
            const id = this.notificationCounter++;

            // Créer un élément DOM pour la notification spéciale
            const notifElement = document.createElement('div');
            notifElement.className = 'toast show text-bg-warning';
            notifElement.style.zIndex = '1060';

            notifElement.innerHTML = `
                <div class="toast-header">
                    <strong class="me-auto">Suggestion de Replay</strong>
                    <button type="button" class="btn-close" aria-label="Close"></button>
                </div>
                <div class="toast-body">
                    <p>${message}</p>
                    <div class="mt-2 pt-2 border-top">
                        <button type="button" class="btn btn-primary btn-sm" id="accept-replay">
                            <i class="bi bi-camera-reels me-1"></i> Lancer un replay
                        </button>
                        <button type="button" class="btn btn-secondary btn-sm" id="reject-replay">
                            Ignorer
                        </button>
                    </div>
                </div>
            `;

            // Ajouter la notification à la page
            const notifContainer = document.querySelector('.position-fixed.top-0.end-0.p-3');
            notifContainer.appendChild(notifElement);

            // Gérer les boutons de la notification
            notifElement.querySelector('#accept-replay').addEventListener('click', () => {
                this.suggestReplayForTotalPoints();
                notifContainer.removeChild(notifElement);
            });

            notifElement.querySelector('#reject-replay, .btn-close').addEventListener('click', () => {
                notifContainer.removeChild(notifElement);
            });

            // Auto-supprimer après 15 secondes
            setTimeout(() => {
                if (notifElement.parentNode === notifContainer) {
                    notifContainer.removeChild(notifElement);
                }
            }, 15000);
        },

        // Méthode pour charger les équipes actuelles depuis la configuration
        async loadTeamNames() {
            try {
                const response = await fetch('/api/setup/teams');
                const data = await response.json();

                if (data.success && data.teams && data.teams.length >= 2) {
                    // Récupérer les noms des deux premières équipes
                    this.teamAName = data.teams[0].name || 'Équipe A';
                    this.teamBName = data.teams[1].name || 'Équipe B';

                    // Mettre à jour le score dans vMix avec les nouveaux noms
                    this.updateScoreInVMix();
                }
            } catch (e) {
                console.error('Erreur lors du chargement des équipes:', e);
                // Utiliser les noms par défaut
            }
        },

        // Marquer automatiquement chaque point pour un ralenti potentiel
        markPointForReplay(pointName) {
            // Si un enregistrement est déjà en cours, marquer le point comme événement
            if (this.isRecordingReplay) {
                // Sauvegarder le nom d'événement actuel
                const currentEventName = this.eventName;

                // Définir le nom de l'événement pour ce point
                this.eventName = pointName;

                // Marquer l'événement
                this.markReplayEvent();

                // Restaurer le nom d'événement précédent
                this.eventName = currentEventName;
            } else {
                // Si aucun enregistrement n'est en cours, démarrer un nouvel enregistrement
                // et se préparer à marquer ce point et les suivants
                this.eventName = pointName;
                this.startReplayRecording();

                // Ajouter une notification discrète pour indiquer que l'enregistrement a commencé
                this.showNotification(`Enregistrement démarré pour "${pointName}"`, 'info', 2000);

                // Marquer ce point après un court délai pour s'assurer que l'enregistrement est démarré
                setTimeout(() => {
                    if (this.isRecordingReplay) {
                        this.markReplayEvent();
                    }
                }, 500);
            }
        }
    },
    mounted() {
        // Charger les inputs au démarrage
        this.loadInputs();

        // Charger les replays existants
        this.loadReplays();

        // Charger les noms des équipes
        this.loadTeamNames();

        // Mettre en place un rafraîchissement périodique
        setInterval(() => {
            this.loadInputs();
        }, 10000); // Rafraîchir toutes les 10 secondes

        // Écouter les événements de socket.io si nécessaire
        const socket = io();
        socket.on('vmix_status_update', (data) => {
            // Rafraîchir les inputs lorsque le statut vMix est mis à jour
            this.loadInputs();
        });

        socket.on('replay_marked', (eventData) => {
            // Ajouter un nouvel événement de replay à la liste
            this.replayEvents.push(eventData);
            this.showNotification(`Nouvel événement de replay reçu: ${eventData.name}`, 'info');
        });

        // Observer les points consécutifs et suggérer un replay si nécessaire
        this.$watch('totalPointsSinceReplay', (newValue, oldValue) => {
            if (newValue >= 3 && newValue > oldValue) {
                // Suggérer un replay après 3 points au total
                this.showTotalPointsReplaySuggestion(newValue);
            }
        });

        // Conserver les observateurs individuels également pour offrir plus de possibilités
        this.$watch('consecutivePointsA', (newValue, oldValue) => {
            if (newValue >= 3 && newValue > oldValue) {
                // Suggérer un replay après 3 points ou plus
                this.showReplaySuggestion('Équipe A', newValue);
            }
        });

        this.$watch('consecutivePointsB', (newValue, oldValue) => {
            if (newValue >= 3 && newValue > oldValue) {
                // Suggérer un replay après 3 points ou plus
                this.showReplaySuggestion('Équipe B', newValue);
            }
        });
    }
}).mount('#diffusion-app');
