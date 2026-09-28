# Structure du projet PZEM2MQTT réorganisée

```
pzem2mqtt/
├── Makefile                      # Commandes principales du projet
├── README.md                     # Documentation principale
├── requirements.txt              # Dépendances Python
│
├── src/                          # Code source principal
│   └── pzem2mqtt.py             # Programme principal (ex getPzemData.py)
│
├── config/                       # Configuration
│   ├── config.example.json      # Configuration d'exemple
│   ├── config.test.json         # Configuration pour tests
│   └── config.json              # Configuration utilisateur
│
├── simulator/                    # Simulateur pour tests
│   └── pzem_simulator.py        # Simulateur PZEM004T Modbus
│
├── tests/                        # Tests automatisés
│   ├── test_communication.py    # Test communication série/Modbus
│   └── test_pzem_function.py    # Test fonctions de lecture PZEM
│
├── scripts/                      # Scripts d'administration
│   ├── install.sh               # Installation automatique
│   ├── uninstall.sh            # Désinstallation
│   ├── pzem2mqtt.service       # Fichier service systemd
│   ├── setup_virtual_ports.sh  # Configuration ports virtuels
│   ├── stop_virtual_ports.sh   # Arrêt ports virtuels
│   ├── test_full.sh            # Test complet automatisé
│   ├── quick_start.sh          # Démarrage rapide dev
│   └── validate.sh             # Validation configuration
│
└── reset/                        # Outils reset PZEM (inchangés)
    ├── docker-compose.yml
    ├── Dockerfile
    ├── requirements.txt
    └── reset.py
```

## Principales améliorations

### ✅ Structure claire et conventionnelle
- **src/** : Code source séparé
- **config/** : Configurations centralisées  
- **tests/** : Tests isolés
- **scripts/** : Outils d'administration
- **simulator/** : Simulateur dédié

### ✅ Makefile intuitif
- `make help` : Aide complète
- `make install` : Installation automatique
- `make run` : Lancement direct
- `make test-simulator` : Test complet
- `make clean` : Nettoyage

### ✅ Séparation des responsabilités
- **Programme principal** : Focus sur la logique métier
- **Simulateur** : Outil de développement indépendant
- **Tests** : Validation automatisée
- **Configuration** : Gestion centralisée

### ✅ Facilité d'utilisation
- Une seule commande pour tout : `make test-simulator`
- Configuration automatique
- Nettoyage automatique
- Documentation claire

### ✅ Conventions respectées
- Structure standard de projet Python
- Séparation code/config/tests
- Scripts d'administration groupés
- Documentation à la racine
