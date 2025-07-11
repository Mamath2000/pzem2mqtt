#!/bin/bash

echo "Installation du service PZEM2MQTT..."

# Vérification que le script est exécuté en root
if [ "$EUID" -ne 0 ]; then 
    echo "Ce script doit être exécuté en tant que root"
    exit 1
fi

# Installation des dépendances système
echo "Installation des dépendances système..."
apt-get update
apt-get install -y python3 python3-pip

# Installation des dépendances Python
echo "Installation des dépendances Python..."
pip3 install -r requirements.txt

# Création du service systemd
echo "Configuration du service systemd..."
cp pzem2mqtt.service /etc/systemd/system/
chmod 644 /etc/systemd/system/pzem2mqtt.service

# Configuration des permissions pour le port série
echo "Configuration des permissions pour le port série..."
usermod -a -G dialout root

# Rechargement de systemd
echo "Rechargement de la configuration systemd..."
systemctl daemon-reload

# Activation et démarrage du service
echo "Activation et démarrage du service..."
systemctl enable pzem2mqtt.service
systemctl start pzem2mqtt.service

# Vérification du statut
echo "Vérification du statut du service..."
systemctl status pzem2mqtt.service

echo "Installation terminée !"
echo "Pour voir les logs en temps réel : journalctl -f -u pzem2mqtt.service"
