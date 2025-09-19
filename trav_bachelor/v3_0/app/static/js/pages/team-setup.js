/**
 * Application de gestion des équipes pour Volleyball Streaming Manager
 * Permet de configurer les équipes pour un match et de gérer la base de données des équipes
 */

// todo review all this code

// Application Vue pour la gestion des équipes
const teamSetupApp = Vue.createApp({
    data() {
        return {
            teams: [],
            teamA: {
                selectedId: '',
                name: '',
                logo: '',
                country: '',
                players: []
            },
            teamB: {
                selectedId: '',
                name: '',
                logo: '',
                country: '',
                players: []
            },
            newTeam: {
                id: null,
                name: '',
                country: '',
                logo: '',
                players: []
            },
            isEditing: false,
            logoFile: null,
            showCsvUpload: false,
            csvFile: null,
            socket: null
        };
    },
    computed: {
        canSetupMatch() {
            return this.teamA.selectedId && this.teamB.selectedId && this.teamA.selectedId !== this.teamB.selectedId;
        }
    },
    methods: {
        // Chargement des équipes
        async loadTeams() {
            try {
                const response = await fetch('/api/teams');
                if (response.ok) {
                    this.teams = await response.json();
                } else {
                    this.showNotification('Erreur lors du chargement des équipes', 'danger');
                }
            } catch (error) {
                console.error('Erreur:', error);
                this.showNotification('Erreur de connexion au serveur', 'danger');
            }
        },

        // Sélection des équipes
        selectTeamA() {
            if (!this.teamA.selectedId) {
                this.teamA = { selectedId: '', name: '', logo: '', country: '', players: [] };
                return;
            }

            const team = this.teams.find(t => t.id === this.teamA.selectedId);
            if (team) {
                this.teamA = {
                    selectedId: team.id,
                    name: team.name,
                    logo: team.logo,
                    country: team.country,
                    players: team.players || []
                };
            }
        },

        selectTeamB() {
            if (!this.teamB.selectedId) {
                this.teamB = { selectedId: '', name: '', logo: '', country: '', players: [] };
                return;
            }

            const team = this.teams.find(t => t.id === this.teamB.selectedId);
            if (team) {
                this.teamB = {
                    selectedId: team.id,
                    name: team.name,
                    logo: team.logo,
                    country: team.country,
                    players: team.players || []
                };
            }
        },

        // Configuration du match
        async setupMatch() {
            if (!this.canSetupMatch) return;

            try {
                const response = await fetch('/api/match/setup-teams', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        teamA: this.teamA.selectedId,
                        teamB: this.teamB.selectedId
                    })
                });

                if (response.ok) {
                    this.showNotification('Configuration du match réussie', 'success');
                    // Redirection vers la page de configuration live
                    window.location.href = '/core/live_setup';
                } else {
                    const error = await response.json();
                    this.showNotification(`Erreur: ${error.message || 'Erreur inconnue'}`, 'danger');
                }
            } catch (error) {
                console.error('Erreur:', error);
                this.showNotification('Erreur de connexion au serveur', 'danger');
            }
        },

        // Gestion des équipes
        editTeam(team) {
            this.isEditing = true;
            this.newTeam = {
                id: team.id,
                name: team.name,
                country: team.country,
                logo: team.logo,
                players: JSON.parse(JSON.stringify(team.players || []))
            };

            // Basculer vers l'onglet de gestion des équipes
            document.querySelector('a[href="#team-management"]').click();
        },

        async deleteTeam(teamId) {
            if (!confirm('Êtes-vous sûr de vouloir supprimer cette équipe ?')) return;

            try {
                const response = await fetch(`/api/teams/${teamId}`, {
                    method: 'DELETE'
                });

                if (response.ok) {
                    this.teams = this.teams.filter(t => t.id !== teamId);
                    this.showNotification('Équipe supprimée avec succès', 'success');

                    // Réinitialiser les sélections si nécessaire
                    if (this.teamA.selectedId === teamId) {
                        this.teamA = { selectedId: '', name: '', logo: '', country: '', players: [] };
                    }
                    if (this.teamB.selectedId === teamId) {
                        this.teamB = { selectedId: '', name: '', logo: '', country: '', players: [] };
                    }
                } else {
                    const error = await response.json();
                    this.showNotification(`Erreur: ${error.message || 'Erreur inconnue'}`, 'danger');
                }
            } catch (error) {
                console.error('Erreur:', error);
                this.showNotification('Erreur de connexion au serveur', 'danger');
            }
        },

        resetForm() {
            this.isEditing = false;
            this.newTeam = {
                id: null,
                name: '',
                country: '',
                logo: '',
                players: []
            };
            this.logoFile = null;
            this.showCsvUpload = false;
            this.csvFile = null;
        },

        async saveTeam() {
            // Préparer les données pour l'envoi
            const formData = new FormData();
            formData.append('name', this.newTeam.name);
            formData.append('country', this.newTeam.country || '');
            formData.append('players', JSON.stringify(this.newTeam.players));

            if (this.logoFile) {
                formData.append('logo', this.logoFile);
            }

            try {
                let url = '/api/teams';
                let method = 'POST';

                if (this.isEditing) {
                    url = `/api/teams/${this.newTeam.id}`;
                    method = 'PUT';
                    formData.append('id', this.newTeam.id);
                }

                const response = await fetch(url, {
                    method: method,
                    body: formData
                });

                if (response.ok) {
                    const result = await response.json();

                    if (this.isEditing) {
                        // Mettre à jour l'équipe dans la liste
                        const index = this.teams.findIndex(t => t.id === result.id);
                        if (index !== -1) {
                            this.teams[index] = result;
                        }
                        this.showNotification('Équipe mise à jour avec succès', 'success');
                    } else {
                        // Ajouter la nouvelle équipe à la liste
                        this.teams.push(result);
                        this.showNotification('Équipe créée avec succès', 'success');
                    }

                    this.resetForm();
                } else {
                    const error = await response.json();
                    this.showNotification(`Erreur: ${error.message || 'Erreur inconnue'}`, 'danger');
                }
            } catch (error) {
                console.error('Erreur:', error);
                this.showNotification('Erreur de connexion au serveur', 'danger');
            }
        },

        // Gestion des joueurs
        addPlayer() {
            this.newTeam.players.push({
                number: '',
                name: '',
                position: 'Attaquant'
            });
        },

        removePlayer(index) {
            this.newTeam.players.splice(index, 1);
        },

        // Gestion des fichiers
        handleLogoUpload(event) {
            this.logoFile = event.target.files[0];
        },

        handleCsvUpload(event) {
            this.csvFile = event.target.files[0];
        },

        async uploadCsv() {
            if (!this.csvFile) {
                this.showNotification('Aucun fichier CSV sélectionné', 'warning');
                return;
            }

            try {
                const formData = new FormData();
                formData.append('csv', this.csvFile);

                const response = await fetch('/api/teams/import-csv', {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    const players = await response.json();
                    this.newTeam.players = players;
                    this.showCsvUpload = false;
                    this.showNotification('Joueurs importés avec succès', 'success');
                } else {
                    const error = await response.json();
                    this.showNotification(`Erreur: ${error.message || 'Erreur inconnue'}`, 'danger');
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

            this.socket.on('teams_updated', () => {
                this.loadTeams();
            });

            this.socket.on('disconnect', () => {
                console.log('Déconnecté du WebSocket');
            });
        }
    },
    mounted() {
        // Charger les équipes au chargement de la page
        this.loadTeams();

        // Configurer le WebSocket
        this.setupWebSocket();
    }
}).mount('#team-setup-app');
