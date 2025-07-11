#!/bin/bash

echo "Installation du service PZEM2MQTT..."

# Vérification que le script est exécuté en root
if [ "$EUID" -ne 0 ]; then 
    echo "Ce script doit être exécuté en tant que root"
    exit 1
fi

# Détection du répertoire d'installation
INSTALL_DIR=$(pwd)
echo "Répertoire d'installation: $INSTALL_DIR"

# Vérification que nous sommes dans le bon répertoire
if [ ! -f "getPzemData.py" ]; then
    echo "Erreur: Fichier getPzemData.py non trouvé dans le répertoire courant"
    echo "Assurez-vous d'être dans le répertoire pzem2mqtt"
    exit 1
fi

# Vérification de la présence du fichier de configuration
if [ ! -f "config.json" ]; then
    if [ -f "config.json.example" ]; then
        echo "Copie du fichier de configuration d'exemple..."
        cp config.json.example config.json
        echo "⚠️  ATTENTION: Veuillez modifier config.json selon votre configuration avant de démarrer le service"
    else
        echo "Erreur: Aucun fichier de configuration trouvé"
        exit 1
    fi
fi

# Installation des dépendances système
echo "Installation des dépendances système..."
apt-get update
apt-get install -y python3 python3-pip

# Installation des dépendances Python
echo "Installation des dépendances Python..."
pip3 install -r requirements.txt

# Mise à jour du fichier de service avec le bon chemin
echo "Configuration du service systemd..."
sed -i "s|WorkingDirectory=.*|WorkingDirectory=$INSTALL_DIR|g" pzem2mqtt.service
sed -i "s|ExecStart=.*|ExecStart=/usr/bin/python3 $INSTALL_DIR/getPzemData.py|g" pzem2mqtt.service

# Copie du service systemd
cp pzem2mqtt.service /etc/systemd/system/
chmod 644 /etc/systemd/system/pzem2mqtt.service

# Configuration des permissions pour le port série
echo "Configuration des permissions pour le port série..."
usermod -a -G dialout root

# Rechargement de systemd
echo "Rechargement de la configuration systemd..."
systemctl daemon-reload

# Activation du service (sans le démarrer automatiquement)
echo "Activation du service..."
systemctl enable pzem2mqtt.service

echo "Installation terminée !"
echo ""
echo "📋 Étapes suivantes:"
echo "1. Vérifiez et modifiez le fichier config.json selon votre configuration"
echo "2. Démarrez le service avec: systemctl start pzem2mqtt.service"
echo "3. Vérifiez le statut avec: systemctl status pzem2mqtt.service" 
echo "4. Consultez les logs avec: journalctl -f -u pzem2mqtt.service"
