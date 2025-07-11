#!/bin/bash

echo "Désinstallation du service PZEM2MQTT..."

# Vérification que le script est exécuté en root
if [ "$EUID" -ne 0 ]; then 
    echo "Ce script doit être exécuté en tant que root"
    exit 1
fi

# Arrêt du service
echo "Arrêt du service..."
systemctl stop pzem2mqtt.service

# Désactivation du service
echo "Désactivation du service..."
systemctl disable pzem2mqtt.service

# Suppression du fichier de service
echo "Suppression du fichier de service..."
rm -f /etc/systemd/system/pzem2mqtt.service

# Rechargement de systemd
echo "Rechargement de la configuration systemd..."
systemctl daemon-reload
systemctl reset-failed

echo "Désinstallation terminée !"
echo ""
echo "Note: Les dépendances Python ne sont pas supprimées automatiquement."
echo "Si vous souhaitez les supprimer, utilisez: pip3 uninstall modbus-tk pyserial paho-mqtt pytz schedule"
