# 🔌 PZEM2MQTT

Script Python pour lire des capteurs PZEM-004T et publier les données vers MQTT avec support Home Assistant.

## 🚀 Démarrage rapide

```bash
# Installation
make install

# Configuration
make config
# Éditez config/config.json selon votre installation

# Test sans matériel physique
make test-simulator

# Utilisation normale
make run

# Service systemd
make start
```

## 📁 Structure du projet

```
pzem2mqtt/
├── src/                    # Code source principal
│   └── pzem2mqtt.py       # Programme principal
├── simulator/             # Simulateur PZEM004T pour tests
│   └── pzem_simulator.py  # Simulateur Modbus
├── tests/                 # Tests automatisés
│   ├── test_communication.py
│   └── test_pzem_function.py
├── scripts/               # Scripts d'installation et utilitaires
│   ├── install.sh
│   ├── uninstall.sh
│   ├── setup_virtual_ports.sh
│   └── test_full.sh
├── config/                # Fichiers de configuration
│   ├── config.example.json
│   ├── config.test.json
│   └── config.json        # Votre configuration
├── reset/                 # Outils de reset PZEM
├── Makefile              # Commandes du projet
└── requirements.txt      # Dépendances Python
```

## 🛠️ Commandes Makefile

### Installation et configuration
- `make install` - Installer le projet et créer le service systemd
- `make uninstall` - Désinstaller complètement
- `make config` - Créer config.json depuis l'exemple
- `make config-test` - Utiliser la configuration de test
- `make config-reset` - Remettre la configuration par défaut

### Utilisation
- `make run` - Lancer le programme directement
- `make start` - Démarrer le service systemd
- `make stop` - Arrêter le service
- `make restart` - Redémarrer le service
- `make status` - Voir le statut du service
- `make logs` - Voir les logs en temps réel

### Tests et développement
- `make test` - Tests basiques
- `make test-simulator` - Test complet avec simulateur
- `make simulator` - Démarrer le simulateur seul
- `make quick-test` - Configuration rapide pour test
- `make setup-dev` - Installer les dépendances de développement
- `make clean` - Nettoyer les fichiers temporaires

## 📝 Configuration

Le fichier `config/config.json` contient tous les paramètres :

```json
{
  "mqtt": {
    "host": "192.168.1.100",
    "port": 1883,
    "auto_discovery": true,
    "discovery_topic": "homeassistant",
    "base_topic": "pzem2mqtt/001"
  },
  "serial": {
    "port": "/dev/ttyUSB0",
    "baudrate": 9600
  },
  "general": {
    "local_tz": "Europe/Paris",
    "poll_interval": 20,
    "log_level": "INFO"
  },
  "sensors": [
    {
      "device_id": 1,
      "unique_id": "sensor_1_energy",
      "name": "Capteur 1",
      "enabled": true
    }
  ]
}
```

## 🧪 Test sans matériel

Pour tester sans capteur PZEM004T physique :

```bash
# Configuration complète automatique
make test-simulator

# Ou étape par étape
make setup-dev
make config-test
make quick-test
make run
```

Le simulateur crée des ports série virtuels et répond comme un vrai PZEM004T.

## 📦 Installation manuelle

Si vous préférez installer sans le Makefile :

```bash
# Dépendances système
sudo apt-get install python3 python3-pip python3-venv socat

# Dépendances Python
pip3 install -r requirements.txt

# Configuration
cp config/config.example.json config/config.json
# Éditez config/config.json

# Test
cd src && python3 pzem2mqtt.py
```

## 🔧 Dépannage

### Erreur de port série
```bash
# Vérifier les ports disponibles
ls /dev/tty*

# Permissions utilisateur
sudo usermod -a -G dialout $USER
```

### Test du simulateur
```bash
# Démarrer le simulateur
make simulator

# Dans un autre terminal, tester
make test
```

### Logs du service
```bash
# Logs en temps réel
make logs

# Statut du service
make status
```

## 📊 Topics MQTT

Les données sont publiées sur : `{base_topic}/{unique_id}`

Format des données :
```json
{
  "current": 2.1,
  "energy": 123.456,
  "power": 500.0,
  "voltage": 230.1,
  "facteur_de_puiss": 0.98,
  "frequency": 50.0,
  "apparent_power": 481.1,
  "timestamp": "2025-07-24T16:30:00.000000",
  "last_read": "2025-07-24 16:30:00"
}
```

## 🏠 Home Assistant

Le programme supporte la découverte automatique Home Assistant. Les capteurs apparaissent automatiquement dans Home Assistant si `auto_discovery` est activé.

## 📄 Licence

Projet open source - voir les détails dans le code source.
