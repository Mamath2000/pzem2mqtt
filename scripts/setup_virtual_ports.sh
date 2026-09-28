#!/bin/bash

# Script pour créer des ports série virtuels pour le test du PZEM004T
# Utilise socat pour créer une paire de ports connectés

echo "=== Configuration des ports série virtuels pour test PZEM004T ==="

# Vérifier si socat est installé
if ! command -v socat &> /dev/null; then
    echo "❌ socat n'est pas installé. Installation en cours..."
    sudo apt-get update
    sudo apt-get install -y socat
    if [ $? -eq 0 ]; then
        echo "✅ socat installé avec succès"
    else
        echo "❌ Erreur lors de l'installation de socat"
        exit 1
    fi
else
    echo "✅ socat est déjà installé"
fi

# Créer le répertoire pour les PTY si nécessaire
mkdir -p /tmp/pzem_test

# Arrêter les processus socat existants (s'il y en a)
echo "🔄 Nettoyage des processus socat existants..."
pkill -f "socat.*pzem"

# Créer les ports série virtuels
echo "🔧 Création des ports série virtuels..."

# Port principal pour la communication PZEM
socat -d -d pty,raw,echo=0,link=/tmp/pzem_test/pzem_device pty,raw,echo=0,link=/tmp/pzem_test/pzem_host &
SOCAT_PID1=$!

# Attendre que les liens soient créés
sleep 2

# Vérifier que les liens ont été créés
if [ -L "/tmp/pzem_test/pzem_device" ] && [ -L "/tmp/pzem_test/pzem_host" ]; then
    echo "✅ Ports série virtuels créés avec succès:"
    echo "   📡 Port pour le simulateur PZEM: /tmp/pzem_test/pzem_device"
    echo "   🖥️  Port pour getPzemData.py:    /tmp/pzem_test/pzem_host"
    
    # Afficher les vrais chemins des périphériques
    REAL_DEVICE=$(readlink /tmp/pzem_test/pzem_device)
    REAL_HOST=$(readlink /tmp/pzem_test/pzem_host)
    echo "   📍 Périphériques réels:"
    echo "      Device: $REAL_DEVICE"
    echo "      Host:   $REAL_HOST"
else
    echo "❌ Erreur lors de la création des ports série virtuels"
    kill $SOCAT_PID1 2>/dev/null
    exit 1
fi

# Sauvegarder le PID pour pouvoir arrêter le processus plus tard
echo $SOCAT_PID1 > /tmp/pzem_test/socat.pid

echo "🎯 Configuration terminée !"
echo ""
echo "📋 Instructions d'utilisation:"
echo "   1. Lancer le simulateur PZEM: make simulator"
echo "   2. Modifier config.json pour utiliser '/tmp/pzem_test/pzem_host'"
echo "   3. Lancer le programme: make run"
echo ""
echo "🛑 Pour arrêter les ports virtuels: make clean"
