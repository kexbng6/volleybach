// Application Vue pour la gestion des équipes
const { createApp } = Vue;

// Configuration du socket.io
let socket;
try {
    socket = io();
    console.log("Socket.IO initialisé avec succès");
} catch (error) {
    console.error("Erreur lors de l'initialisation de Socket.IO:", error);
    // Simuler un objet socket pour éviter les erreurs
    socket = {
        on: function() {
            console.log("Socket.IO non disponible - événement ignoré");
        },
        emit: function() {
            console.log("Socket.IO non disponible - émission ignorée");
        }
    };
}

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
            console.log(`Notification ajoutée: ${message} (${type})`);

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
            console.log("Chargement des équipes...");
            fetch('/api/teams')
                .then(response => {
                    console.log("Réponse reçue:", response);
                    return response.json();
                })
                .then(data => {
                    console.log("Données reçues:", data);
                    this.teams = data.teams || [];
                    this.addNotification(`${this.teams.length} équipes chargées`, 'info');
                })
                .catch(error => {
                    console.error("Erreur lors du chargement des équipes:", error);
                    this.addNotification(`Erreur lors du chargement des équipes: ${error.message}`, 'danger');
                });
        },

        // Créer une nouvelle équipe (depuis la section gestion des équipes)
        createTeam(event) {
            event.preventDefault();
            console.log("Création d'une nouvelle équipe:", this.newTeam);

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

            fetch('/api/teams/create', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                console.log("Réponse reçue:", response);
                return response.json();
            })
            .then(data => {
                console.log("Données reçues:", data);
                if (data.error) {
                    this.addNotification(data.error, 'danger');
                } else {
                    this.addNotification(data.message || 'Équipe créée avec succès', 'success');
                    this.newTeam = { name: '', logo: null, players: null };

                    // Recharger les équipes si le serveur n'envoie pas de socket
                    if (!data.team) {
                        this.loadTeams();
                    }
                }
            })
            .catch(error => {
                console.error("Erreur lors de la création de l'équipe:", error);
                this.addNotification(`Erreur lors de la création de l'équipe: ${error.message}`, 'danger');
            });
        },

        // Afficher les détails d'une équipe
        viewTeam(team) {
            console.log("Affichage des détails de l'équipe:", team);
            this.selectedTeamId = team.id;
            this.loadTeamPlayers();
        },

        // Supprimer une équipe
        deleteTeam(team) {
            if (confirm(`Êtes-vous sûr de vouloir supprimer l'équipe "${team.name}" ?`)) {
                console.log("Suppression de l'équipe:", team);
                fetch(`/api/teams/${team.id}/delete`, {
                    method: 'DELETE'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        this.addNotification(data.error, 'danger');
                    } else {
                        this.addNotification(data.message || 'Équipe supprimée avec succès', 'success');

                        // Si le serveur ne supprime pas via socket, supprimons manuellement
                        if (!data.socketUpdated) {
                            const index = this.teams.findIndex(t => t.id === team.id);
                            if (index !== -1) {
                                this.teams.splice(index, 1);
                            }
                        }
                    }
                })
                .catch(error => {
                    console.error("Erreur lors de la suppression de l'équipe:", error);
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

            console.log("Chargement des joueurs pour l'équipe:", this.selectedTeamId);
            fetch(`/api/teams/${this.selectedTeamId}/players`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        this.addNotification(data.error, 'danger');
                    } else {
                        this.teamPlayers = data.players || [];
                        this.selectedPlayerId = '';
                        console.log("Joueurs chargés:", this.teamPlayers);
                    }
                })
                .catch(error => {
                    console.error("Erreur lors du chargement des joueurs:", error);
                    this.addNotification(`Erreur lors du chargement des joueurs: ${error.message}`, 'danger');
                });
        },

        // Sélectionner une équipe existante pour l'équipe A
        selectTeamA() {
            if (!this.teamA.selectedId) {
                this.teamA = {
                    selectedId: '',
                    createNew: false,
                    name: '',
                    logo: null,
                    players: null,
                    playerCount: 0
                };
                return;
            }

            // Récupérer les détails de l'équipe sélectionnée
            const selectedTeam = this.teams.find(team => team.id === this.teamA.selectedId);
            if (selectedTeam) {
                console.log("Équipe A sélectionnée:", selectedTeam);
                this.teamA.name = selectedTeam.name;
                this.teamA.logo = selectedTeam.logo;
                this.teamA.playerCount = selectedTeam.players ? selectedTeam.players.length : 0;
                this.teamA.createNew = false;

                // Récupérer les joueurs si nécessaire
                if (!selectedTeam.players || selectedTeam.players.length === 0) {
                    fetch(`/api/teams/${selectedTeam.id}/players`)
                        .then(response => response.json())
                        .then(data => {
                            if (!data.error) {
                                this.teamA.players = data.players;
                                this.teamA.playerCount = data.players.length;
                                console.log("Joueurs de l'équipe A chargés:", data.players);
                            }
                        })
                        .catch(error => {
                            console.error("Erreur lors du chargement des joueurs:", error);
                            this.addNotification(`Erreur lors du chargement des joueurs: ${error.message}`, 'danger');
                        });
                } else {
                    this.teamA.players = selectedTeam.players;
                }
            }
        },

        // Sélectionner une équipe existante pour l'équipe B
        selectTeamB() {
            if (!this.teamB.selectedId) {
                this.teamB = {
                    selectedId: '',
                    createNew: false,
                    name: '',
                    logo: null,
                    players: null,
                    playerCount: 0
                };
                return;
            }

            // Récupérer les détails de l'équipe sélectionnée
            const selectedTeam = this.teams.find(team => team.id === this.teamB.selectedId);
            if (selectedTeam) {
                console.log("Équipe B sélectionnée:", selectedTeam);
                this.teamB.name = selectedTeam.name;
                this.teamB.logo = selectedTeam.logo;
                this.teamB.playerCount = selectedTeam.players ? selectedTeam.players.length : 0;
                this.teamB.createNew = false;

                // Récupérer les joueurs si nécessaire
                if (!selectedTeam.players || selectedTeam.players.length === 0) {
                    fetch(`/api/teams/${selectedTeam.id}/players`)
                        .then(response => response.json())
                        .then(data => {
                            if (!data.error) {
                                this.teamB.players = data.players;
                                this.teamB.playerCount = data.players.length;
                                console.log("Joueurs de l'équipe B chargés:", data.players);
                            }
                        })
                        .catch(error => {
                            console.error("Erreur lors du chargement des joueurs:", error);
                            this.addNotification(`Erreur lors du chargement des joueurs: ${error.message}`, 'danger');
                        });
                } else {
                    this.teamB.players = selectedTeam.players;
                }
            }
        },

        // Gérer l'upload du logo d'une équipe
        handleLogoUpload(team, event) {
            const file = event.target.files[0];
            if (!file) return;

            // Vérifier que c'est bien une image
            if (!file.type.match('image.*')) {
                this.addNotification('Veuillez sélectionner une image valide (JPG, PNG)', 'warning');
                event.target.value = ''; // Réinitialiser l'input
                return;
            }

            console.log(`Logo uploadé pour l'équipe ${team}:`, file.name);

            // Stocker le fichier
            if (team === 'A') {
                this.teamA.logo = file;
            } else if (team === 'B') {
                this.teamB.logo = file;
            }
        },

        // Gérer l'upload du CSV des joueurs
        handleCsvUpload(team, event) {
            const file = event.target.files[0];
            if (!file) return;

            // Vérifier que c'est bien un CSV
            if (file.type !== 'text/csv' && !file.name.endsWith('.csv')) {
                this.addNotification('Veuillez sélectionner un fichier CSV valide', 'warning');
                event.target.value = ''; // Réinitialiser l'input
                return;
            }

            console.log(`CSV uploadé pour l'équipe ${team}:`, file.name);

            // Stocker le fichier
            if (team === 'A') {
                this.teamA.players = file;
            } else if (team === 'B') {
                this.teamB.players = file;
            }
        },

        // Enregistrer une équipe nouvellement créée (à partir des panneaux A ou B)
        saveTeam(team) {
            const teamData = team === 'A' ? this.teamA : this.teamB;
            
            if (!teamData.name) {
                this.addNotification('Veuillez saisir un nom d\'équipe', 'warning');
                return;
            }

            console.log(`Enregistrement de l'équipe ${team}:`, teamData);

            const formData = new FormData();
            formData.append('team_name', teamData.name);

            if (teamData.logo) {
                formData.append('team_logo', teamData.logo);
                console.log("Logo ajouté au FormData:", teamData.logo.name);
            }

            if (teamData.players) {
                formData.append('players_csv', teamData.players);
                console.log("CSV ajouté au FormData:", teamData.players.name);
            }

            // Afficher le contenu du FormData pour le débogage
            console.log("FormData créé:");
            for (const pair of formData.entries()) {
                console.log(`${pair[0]}: ${pair[1]}`);
            }

            fetch('/api/teams/create', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                console.log("Réponse reçue:", response);
                return response.json();
            })
            .then(data => {
                console.log("Données reçues:", data);
                if (data.error) {
                    this.addNotification(data.error, 'danger');
                } else {
                    this.addNotification(data.message || 'Équipe créée avec succès', 'success');
                    
                    // Ajouter l'équipe à la liste locale si elle n'y est pas déjà
                    if (data.team && !this.teams.find(t => t.id === data.team.id)) {
                        this.teams.push(data.team);
                    } else {
                        // Recharger les équipes si le serveur n'a pas renvoyé les données de l'équipe
                        this.loadTeams();
                    }
                    
                    // Sélectionner automatiquement l'équipe créée
                    if (team === 'A') {
                        this.teamA.selectedId = data.team.id;
                        this.teamA.createNew = false;
                        this.selectTeamA();
                    } else if (team === 'B') {
                        this.teamB.selectedId = data.team.id;
                        this.teamB.createNew = false;
                        this.selectTeamB();
                    }
                }
            })
            .catch(error => {
                console.error("Erreur lors de la création de l'équipe:", error);
                this.addNotification(`Erreur lors de la création de l'équipe: ${error.message}`, 'danger');
            });
        },

        // Configurer les équipes pour le match
        saveMatchTeams() {
            // Vérifier que les deux équipes sont sélectionnées ou en cours de création
            if ((!this.teamA.selectedId && !this.teamA.createNew) || (!this.teamB.selectedId && !this.teamB.createNew)) {
                this.addNotification('Veuillez sélectionner ou créer les deux équipes pour ce match', 'warning');
                return;
            }

            console.log("Configuration du match avec les équipes:", {
                teamA: this.teamA,
                teamB: this.teamB
            });

            // Si des nouvelles équipes sont en cours de création, les sauvegarder d'abord
            const promises = [];
            
            if (this.teamA.createNew && this.teamA.name) {
                promises.push(new Promise(resolve => {
                    this.saveTeam('A');
                    resolve();
                }));
            }
            
            if (this.teamB.createNew && this.teamB.name) {
                promises.push(new Promise(resolve => {
                    this.saveTeam('B');
                    resolve();
                }));
            }

            // Une fois les équipes sauvegardées, configurer le match
            Promise.all(promises).then(() => {
                // Préparer les données pour la configuration du match
                const matchData = {
                    teamA: {
                        id: this.teamA.selectedId,
                        createNew: this.teamA.createNew,
                        name: this.teamA.name
                    },
                    teamB: {
                        id: this.teamB.selectedId,
                        createNew: this.teamB.createNew,
                        name: this.teamB.name
                    }
                };

                // Envoyer la configuration au serveur
                fetch('/api/teams/match/configure', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(matchData)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        this.addNotification(data.error, 'danger');
                    } else {
                        this.addNotification(data.message || 'Match configuré avec succès', 'success');
                        // Redirection si spécifiée
                        if (data.redirect) {
                            window.location.href = data.redirect;
                        }
                    }
                })
                .catch(error => {
                    console.error("Erreur lors de la configuration du match:", error);
                    this.addNotification(`Erreur lors de la configuration du match: ${error.message}`, 'danger');
                });
            });
        },

        // Envoyer le roster d'une équipe vers vMix
        sendRosterToVmix(team) {
            const teamData = team === 'A' ? this.teamA : this.teamB;
            
            if (!teamData.selectedId && !teamData.createNew) {
                this.addNotification('Veuillez sélectionner ou créer une équipe d\'abord', 'warning');
                return;
            }

            // Si c'est une nouvelle équipe, s'assurer qu'elle a des joueurs
            if (teamData.createNew && !teamData.players) {
                this.addNotification('Veuillez ajouter une liste de joueurs pour cette équipe', 'warning');
                return;
            }

            console.log(`Envoi du roster de l'équipe ${team} vers vMix:`, teamData);

            // Préparer les données
            const formData = new FormData();
            
            if (teamData.selectedId) {
                formData.append('team_id', teamData.selectedId);
            } else {
                // Si c'est une nouvelle équipe, envoyer ses données
                formData.append('team_name', teamData.name);
                if (teamData.logo) formData.append('team_logo', teamData.logo);
                if (teamData.players) formData.append('players_csv', teamData.players);
            }
            
            formData.append('team_position', team); // A pour domicile, B pour visiteur

            // Envoyer vers vMix
            fetch('/api/vmix/send-roster', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    this.addNotification(data.error, 'danger');
                } else {
                    this.addNotification(data.message || 'Roster envoyé avec succès vers vMix', 'success');
                }
            })
            .catch(error => {
                console.error("Erreur lors de l'envoi du roster vers vMix:", error);
                this.addNotification(`Erreur lors de l'envoi du roster vers vMix: ${error.message}`, 'danger');
            });
        },

        // Afficher les détails d'un joueur dans vMix
        showPlayerDetailsInVmix() {
            if (!this.selectedTeamId || this.selectedPlayerId === '') {
                this.addNotification('Veuillez sélectionner un joueur', 'warning');
                return;
            }

            const player = this.teamPlayers[this.selectedPlayerId];
            console.log("Affichage des détails du joueur dans vMix:", player);
            
            fetch('/api/vmix/player-details', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    team_id: this.selectedTeamId,
                    player: player
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    this.addNotification(data.error, 'danger');
                } else {
                    this.addNotification(data.message || 'Détails du joueur affichés dans vMix', 'success');
                }
            })
            .catch(error => {
                console.error("Erreur lors de l'affichage des détails du joueur:", error);
                this.addNotification(`Erreur lors de l'affichage des détails du joueur: ${error.message}`, 'danger');
            });
        }
    }
}).mount('#setup-team-app');
