# PZEM2MQTT

Script Python pour lire des capteurs PZEM-004T et publier les données vers MQTT avec support Home Assistant.

## Configuration

Le script utilise un fichier `config.json` pour définir tous les paramètres :

### Structure du fichier config.json

```json
{
  "mqtt": {
    "host": "192.168.100.9",
    "port": 1883,
    "auto_discovery": true,
    "discovery_topic": "homeassistant",
    "base_topic": "pzem2mqtt/003"
  },
  "serial": {
    "port": "/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0",
    "baudrate": 9600
  },
  "general": {
    "local_tz": "Europe/Paris",
    "poll_interval": 5,
    "log_level": "INFO"
  },
  "sensors": [
    {
      "device_id": 1,
      "unique_id": "plaque_induction_energy",
      "name": "Plaque Induction",
      "enabled": true
    },
    {
      "device_id": 2,
      "unique_id": "chauffe_eau_energy",
      "name": "Chauffe Eau",
      "enabled": false
    }
  ]
}
```

### Paramètres de configuration

#### Section MQTT
- `host` : Adresse IP du broker MQTT
- `port` : Port du broker MQTT
- `auto_discovery` : Active/désactive la découverte automatique Home Assistant
- `discovery_topic` : Topic de découverte Home Assistant (généralement "homeassistant")
- `base_topic` : Topic de base pour les publications de données

#### Section Serial
- `port` : Port série pour la communication avec les capteurs PZEM
- `baudrate` : Vitesse de communication (généralement 9600 pour PZEM-004T)

#### Section General
- `local_tz` : Fuseau horaire local
- `poll_interval` : Intervalle de lecture des capteurs en secondes
- `log_level` : Niveau de logging (DEBUG, INFO, WARNING, ERROR)

#### Section Sensors
Liste des capteurs PZEM-004T connectés :
- `device_id` : ID Modbus du capteur (1-247)
- `unique_id` : Identifiant unique pour MQTT et Home Assistant
- `name` : Nom affiché dans Home Assistant
- `enabled` : Active/désactive la lecture de ce capteur

## Installation

### Installation automatique

1. Clonez ou téléchargez le projet :
```bash
git clone https://github.com/Mamath2000/pzem2mqtt.git
cd pzem2mqtt
```

2. Copiez et configurez le fichier de configuration :
```bash
cp config.json.example config.json
# Modifiez config.json selon votre installation
```

3. Lancez l'installation automatique :
```bash
chmod +x install.sh
sudo ./install.sh
```

4. Démarrez le service :
```bash
sudo systemctl start pzem2mqtt.service
```

### Installation manuelle

Si vous préférez installer manuellement :

```bash
# Installation des dépendances
sudo apt-get update
sudo apt-get install -y python3 python3-pip
pip3 install -r requirements.txt

# Configuration
cp config.json.example config.json
# Modifiez config.json selon votre installation

# Test
python3 getPzemData.py
```

## Utilisation

1. Copiez le fichier `config.json` et modifiez-le selon votre installation
2. Lancez le script : `python3 getPzemData.py`

## Ajout de nouveaux capteurs

Pour ajouter un nouveau capteur PZEM-004T :

1. Configurez l'ID Modbus du nouveau capteur (via les boutons du PZEM)
2. Ajoutez une entrée dans la section `sensors` du fichier `config.json`
3. Redémarrez le script

Exemple d'ajout :
```json
{
  "device_id": 5,
  "unique_id": "nouveau_capteur_energy",
  "name": "Nouveau Capteur",
  "enabled": true
}
```

## Désactivation temporaire d'un capteur

Pour désactiver temporairement un capteur sans le supprimer de la configuration, changez `enabled` à `false` dans le fichier de configuration.

## Topics MQTT

Les données sont publiées sur : `{base_topic}/{unique_id}`

Exemple : `pzem2mqtt/003/plaque_induction_energy`

Format des données :
```json
{
  "current": 2.1,
  "energy": 123.456,
  "power": 500.0,
  "voltage": 230.1,
  "facteur_de_puiss": 0.98
}
```

## Gestion du service

### Commandes utiles

```bash
# Démarrer le service
sudo systemctl start pzem2mqtt.service

# Arrêter le service
sudo systemctl stop pzem2mqtt.service

# Redémarrer le service
sudo systemctl restart pzem2mqtt.service

# Voir le statut du service
sudo systemctl status pzem2mqtt.service

# Voir les logs en temps réel
sudo journalctl -f -u pzem2mqtt.service

# Voir les logs depuis le début
sudo journalctl -u pzem2mqtt.service
```

### Désinstallation

Pour désinstaller complètement le service :

```bash
chmod +x uninstall.sh
sudo ./uninstall.sh
```
