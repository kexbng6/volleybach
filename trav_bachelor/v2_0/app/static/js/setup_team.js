document.addEventListener('DOMContentLoaded', function() {
    const teamForm = document.getElementById('team-form');
    const messageDiv = document.getElementById('message');

    // Vérifier si l'élément teamForm existe avant d'ajouter un écouteur d'événement
    if (teamForm) {
        teamForm.addEventListener('submit', function(e) {
            e.preventDefault();

            // Créer un FormData pour envoyer les fichiers
            const formData = new FormData(teamForm);

            // Envoyer les données au serveur avec le bon chemin
            fetch('/team/create_team', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    messageDiv.innerHTML = `<div class="error">${data.error}</div>`;
                } else {
                    messageDiv.innerHTML = `<div class="success">${data.message}</div>`;
                    // Réinitialiser le formulaire
                    teamForm.reset();
                }
            })
            .catch(error => {
                messageDiv.innerHTML = `<div class="error">Erreur: ${error.message}</div>`;
            });
        });
    }
});

// Configuration du socket.io
const socket = io();

// Application Vue pour la gestion des équipes
const { createApp } = Vue;

createApp({
    data() {
        return {
            // Gestion des notifications
            notifications: [],
            notificationId: 0,

            // Liste des équipes existantes
            teams: [],

            // Nouvelle équipe (pour l'ajout d'équipe)
            newTeam: {
                name: '',
                logo: null,
                players: null
            },

            // Équipe A (domicile)
            teamA: {
                selectedId: '',
                createNew: false,
                name: '',
                logo: null,
                players: null,
                playerCount: 0
            },

            // Équipe B (visiteur)
            teamB: {
                selectedId: '',
                createNew: false,
                name: '',
                logo: null,
                players: null,
                playerCount: 0
            },

            // Sélection des joueurs pour l'affichage des détails
            selectedTeamId: '',
            teamPlayers: [],
            selectedPlayerId: ''
        }
    },

    computed: {
        // Propriété calculée pour obtenir les détails du joueur sélectionné
        selectedPlayer() {
            if (this.selectedPlayerId === '' || !this.teamPlayers[this.selectedPlayerId]) {
                return {};
            }
            return this.teamPlayers[this.selectedPlayerId];
        }
    },

    mounted() {
        // Charger la liste des équipes existantes
        this.loadTeams();

        // Écouter les événements socket
        socket.on('connect', () => {
            this.addNotification('Connexion établie avec le serveur', 'success');
        });

        socket.on('disconnect', () => {
            this.addNotification('Connexion perdue avec le serveur', 'danger');
        });

        // Configuration du socket.io et gestion des événements
        socket.on('team_created', (teamData) => {
            this.addNotification(`L'équipe "${teamData.name}" a été créée avec succès`, 'success');
            this.teams.push(teamData);
        });

        socket.on('team_updated', (teamData) => {
            const index = this.teams.findIndex(team => team.id === teamData.id);
            if (index !== -1) {
                this.teams[index] = teamData;
                this.addNotification(`L'équipe "${teamData.name}" a été mise à jour`, 'success');
            }
        });

        socket.on('team_deleted', (data) => {
            const index = this.teams.findIndex(team => team.id === data.id);
            if (index !== -1) {
                const teamName = this.teams[index].name;
                this.teams.splice(index, 1);
                this.addNotification(`L'équipe "${teamName}" a été supprimée`, 'warning');
            }
        });

        // Initialiser la navigation par onglets
        this.initTabs();
    },

    methods: {
        // Gestion des notifications
        addNotification(message, type = 'info') {
            const id = this.notificationId++;
            this.notifications.push({ id, message, type });

            // Supprimer automatiquement après 5 secondes
            setTimeout(() => {
                this.notifications = this.notifications.filter(n => n.id !== id);
            }, 5000);
        },

        // Initialiser la navigation par onglets
        initTabs() {
            document.querySelectorAll('.nav-link').forEach(link => {
                link.addEventListener('click', (e) => {
                    e.preventDefault();

                    // Retirer la classe active de tous les liens
                    document.querySelectorAll('.nav-link').forEach(l => {
                        l.classList.remove('active');
                    });

                    // Ajouter la classe active au lien cliqué
                    e.target.classList.add('active');

                    // Afficher la section correspondante
                    const targetId = e.target.getAttribute('href');
                    document.querySelectorAll('.card').forEach(card => {
                        if (card.id && card.id === targetId.substring(1)) {
                            card.style.display = 'block';
                        } else if (card.id) {
                            card.style.display = 'none';
                        }
                    });
                });
            });
        },

        // Charger la liste des équipes existantes
        loadTeams() {
            fetch('/team/teams')
                .then(response => response.json())
                .then(data => {
                    this.teams = data.teams || [];
                })
                .catch(error => {
                    this.addNotification(`Erreur lors du chargement des équipes: ${error.message}`, 'danger');
                });
        },

        // Créer une nouvelle équipe (depuis la section gestion des équipes)
        createTeam(event) {
            event.preventDefault();

            if (!this.newTeam.name) {
                this.addNotification('Veuillez saisir un nom d\'équipe', 'warning');
                return;
            }

            const formData = new FormData();
            formData.append('team_name', this.newTeam.name);

            if (this.newTeam.logo) {
                formData.append('team_logo', this.newTeam.logo);
            }

            if (this.newTeam.players) {
                formData.append('players_csv', this.newTeam.players);
            }

            // Envoi via l'API
            fetch('/team/create_team', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    this.addNotification(data.error, 'danger');
                } else {
                    this.addNotification(`Équipe "${this.newTeam.name}" créée avec succès`, 'success');
                    // Réinitialisation du formulaire
                    this.newTeam.name = '';
                    this.newTeam.logo = null;
                    this.newTeam.players = null;
                    document.getElementById('team_logo').value = '';
                    document.getElementById('players_csv').value = '';
                }
            })
            .catch(error => {
                this.addNotification(`Erreur lors de la création de l'équipe: ${error.message}`, 'danger');
            });
        },

        // Gérer l'upload du logo pour la nouvelle équipe
        handleNewTeamLogoUpload(event) {
            this.newTeam.logo = event.target.files[0];
        },

        // Gérer l'upload du fichier CSV pour la nouvelle équipe
        handleNewTeamCsvUpload(event) {
            this.newTeam.players = event.target.files[0];
        },

        // Gérer l'upload du logo pour les équipes A et B
        handleLogoUpload(team, event) {
            const file = event.target.files[0];
            if (team === 'A') {
                this.teamA.logo = file;
            } else if (team === 'B') {
                this.teamB.logo = file;
            }
        },

        // Gérer l'upload du fichier CSV pour les équipes A et B
        handleCsvUpload(team, event) {
            const file = event.target.files[0];
            if (team === 'A') {
                this.teamA.players = file;
            } else if (team === 'B') {
                this.teamB.players = file;
            }
        },

        // Sélectionner une équipe existante comme équipe A
        selectTeamA() {
            if (!this.teamA.selectedId) return;

            // Désactiver la création d'une nouvelle équipe si une équipe existante est sélectionnée
            if (this.teamA.selectedId) {
                this.teamA.createNew = false;
            }

            // Trouver l'équipe dans la liste
            const selectedTeam = this.teams.find(team => team.id === this.teamA.selectedId);
            if (selectedTeam) {
                this.teamA.name = selectedTeam.name;
                this.teamA.logo = selectedTeam.logo;
                this.teamA.playerCount = selectedTeam.players ? selectedTeam.players.length : 0;
            }
        },

        // Sélectionner une équipe existante comme équipe B
        selectTeamB() {
            if (!this.teamB.selectedId) return;

            // Désactiver la création d'une nouvelle équipe si une équipe existante est sélectionnée
            if (this.teamB.selectedId) {
                this.teamB.createNew = false;
            }

            // Trouver l'équipe dans la liste
            const selectedTeam = this.teams.find(team => team.id === this.teamB.selectedId);
            if (selectedTeam) {
                this.teamB.name = selectedTeam.name;
                this.teamB.logo = selectedTeam.logo;
                this.teamB.playerCount = selectedTeam.players ? selectedTeam.players.length : 0;
            }
        },

        // Envoyer le roster vers vMix
        async sendRosterToVmix(team) {
            let teamData = team === 'A' ? this.teamA : this.teamB;

            if (!teamData.players) {
                this.addNotification('Aucun fichier CSV de joueurs sélectionné', 'warning');
                return;
            }

            if (!teamData.name) {
                this.addNotification('Veuillez saisir un nom d\'équipe', 'warning');
                return;
            }

            try {
                // Créer un FormData pour envoyer le fichier CSV et les informations de l'équipe
                const formData = new FormData();
                formData.append('csvFile', teamData.players);
                formData.append('teamName', teamData.name);

                // Ajouter le logo si disponible
                if (teamData.logo) {
                    formData.append('teamLogo', teamData.logo);
                }

                // Faire une requête pour récupérer les titres vMix disponibles
                const titlesResponse = await fetch('/api/vmix-inputs');
                const titlesData = await titlesResponse.json();

                // Chercher le titre "roster.gtzip" parmi les inputs
                let rosterTitleInput = null;
                if (titlesData.success && titlesData.inputs) {
                    // Chercher un input qui contient "roster" dans son nom
                    rosterTitleInput = titlesData.inputs.find(input =>
                        input.name && input.name.toLowerCase().includes('roster'));
                }

                if (!rosterTitleInput) {
                    this.addNotification('Impossible de trouver le titre "roster" dans vMix. Assurez-vous qu\'il est chargé.', 'danger');
                    return;
                }

                // Ajouter l'ID du titre vMix au formData
                formData.append('titleInput', rosterTitleInput.id);

                // Envoyer les données au serveur pour mise à jour dans vMix
                const response = await fetch('/team/update_roster_in_vmix', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (data.success) {
                    this.addNotification(`Liste de joueurs de ${teamData.name} envoyée vers vMix avec succès`, 'success');
                } else {
                    this.addNotification(`Erreur: ${data.error || 'Échec de la mise à jour dans vMix'}`, 'danger');
                }
            } catch (error) {
                this.addNotification(`Erreur lors de l'envoi des données: ${error.message}`, 'danger');
            }
        },

        // Configurer les équipes pour le match
        saveMatchTeams() {
            // Valider que les équipes A et B sont configurées
            if ((!this.teamA.selectedId && !this.teamA.createNew) ||
                (!this.teamB.selectedId && !this.teamB.createNew)) {
                this.addNotification('Veuillez configurer les deux équipes pour le match', 'warning');
                return;
            }

            // Valider que les noms des nouvelles équipes sont renseignés
            if ((this.teamA.createNew && !this.teamA.name) ||
                (this.teamB.createNew && !this.teamB.name)) {
                this.addNotification('Veuillez saisir le nom des équipes', 'warning');
                return;
            }

            // Vérifier que les équipes sont différentes
            if (!this.teamA.createNew && !this.teamB.createNew &&
                this.teamA.selectedId === this.teamB.selectedId) {
                this.addNotification('Veuillez sélectionner deux équipes différentes', 'warning');
                return;
            }

            // Construire les données à envoyer
            const matchData = {
                teamA: this.teamA.createNew ? null : this.teamA.selectedId,
                teamB: this.teamB.createNew ? null : this.teamB.selectedId,
                newTeamA: this.teamA.createNew ? { name: this.teamA.name } : null,
                newTeamB: this.teamB.createNew ? { name: this.teamB.name } : null
            };

            // Créer un FormData pour les fichiers si nécessaire
            const formData = new FormData();
            formData.append('match_data', JSON.stringify(matchData));

            // Ajouter les fichiers pour la nouvelle équipe A si nécessaire
            if (this.teamA.createNew) {
                if (this.teamA.logo) formData.append('teamA_logo', this.teamA.logo);
                if (this.teamA.players) formData.append('teamA_players', this.teamA.players);
            }

            // Ajouter les fichiers pour la nouvelle équipe B si nécessaire
            if (this.teamB.createNew) {
                if (this.teamB.logo) formData.append('teamB_logo', this.teamB.logo);
                if (this.teamB.players) formData.append('teamB_players', this.teamB.players);
            }

            // Envoyer les données au serveur
            fetch('/api/match/setup-teams', {
                method: 'POST',
                body: formData
            })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        this.addNotification(data.error, 'danger');
                    } else {
                        this.addNotification('Configuration des équipes du match enregistrée avec succès', 'success');
                        // Rediriger vers la page de configuration du match si nécessaire
                        if (data.redirect) {
                            window.location.href = data.redirect;
                        }
                    }
                })
                .catch(error => {
                    this.addNotification(`Erreur lors de la configuration des équipes: ${error.message}`, 'danger');
                });
        },

        // Voir les détails d'une équipe
        viewTeam(team) {
            // À implémenter: afficher une modal avec les détails de l'équipe
            this.addNotification(`Affichage des détails de l'équipe "${team.name}" - Fonctionnalité à venir`, 'info');
        },

        // Supprimer une équipe
        deleteTeam(team) {
            if (confirm(`Êtes-vous sûr de vouloir supprimer l'équipe "${team.name}" ?`)) {
                fetch(`/team/teams/${team.id}`, {
                    method: 'DELETE'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        this.addNotification(data.error, 'danger');
                    }
                    // La mise à jour de la liste sera gérée par l'événement WebSocket team_deleted
                })
                .catch(error => {
                    this.addNotification(`Erreur lors de la suppression de l'équipe: ${error.message}`, 'danger');
                });
            }
        },

        // Charger les joueurs d'une équipe sélectionnée
        loadTeamPlayers() {
            if (!this.selectedTeamId) {
                this.teamPlayers = [];
                this.selectedPlayerId = '';
                return;
            }

            const selectedTeam = this.teams.find(team => team.id === this.selectedTeamId);
            if (selectedTeam && selectedTeam.players) {
                this.teamPlayers = selectedTeam.players;
                this.selectedPlayerId = ''; // Réinitialiser la sélection du joueur
            } else {
                this.teamPlayers = [];
                this.selectedPlayerId = '';
                this.addNotification('Aucun joueur trouvé pour cette équipe', 'warning');
            }
        },

        // Envoyer les détails d'un joueur vers vMix
        async showPlayerDetailsInVmix() {
            if (this.selectedPlayerId === '') {
                this.addNotification('Veuillez sélectionner un joueur', 'warning');
                return;
            }

            const player = this.teamPlayers[this.selectedPlayerId];
            if (!player) {
                this.addNotification('Joueur non trouvé', 'danger');
                return;
            }

            try {
                // Faire une requête pour récupérer les titres vMix disponibles
                const titlesResponse = await fetch('/api/vmix-inputs');
                const titlesData = await titlesResponse.json();

                // Chercher le titre "detailPlayer.gtzip" parmi les inputs
                let detailPlayerTitleInput = null;
                if (titlesData.success && titlesData.inputs) {
                    // Chercher un input qui contient "detailPlayer" dans son nom
                    detailPlayerTitleInput = titlesData.inputs.find(input =>
                        input.name && input.name.toLowerCase().includes('detailplayer'));
                }

                if (!detailPlayerTitleInput) {
                    this.addNotification('Impossible de trouver le titre "detailPlayer" dans vMix. Assurez-vous qu\'il est chargé.', 'danger');
                    return;
                }

                // Préparer les données du joueur à envoyer
                const playerData = {
                    ...player,
                    titleInput: detailPlayerTitleInput.id
                };

                // Envoyer les données au serveur
                const response = await fetch('/team/show_player_details_in_vmix', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(playerData)
                });

                const data = await response.json();

                if (data.success) {
                    this.addNotification(`Détails du joueur ${player.prenom} ${player.nom.toUpperCase()} affichés dans vMix avec succès`, 'success');
                } else {
                    this.addNotification(`Erreur: ${data.error || 'Échec de l\'affichage des détails du joueur dans vMix'}`, 'danger');
                }
            } catch (error) {
                this.addNotification(`Erreur lors de l'envoi des détails du joueur: ${error.message}`, 'danger');
            }
        }
    }
}).mount('#setup-team-app');
