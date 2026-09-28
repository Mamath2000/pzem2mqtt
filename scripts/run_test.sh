#!/bin/bash

# Script de test complet pour l'environnement PZEM2MQTT

echo "🧪 === Test Environment PZEM2MQTT ==="
echo ""

# Fonction pour nettoyer en cas d'arrêt
cleanup() {
    echo ""
    echo "🧹 Nettoyage en cours..."
    
    # Arrêter le simulateur
    if [ ! -z "$SIMULATOR_PID" ]; then
        kill $SIMULATOR_PID 2>/dev/null
        echo "   ✅ Simulateur arrêté"
    fi
    
    # Arrêter les ports virtuels
    ./test_environment/stop_virtual_ports.sh
    
    echo "🏁 Test terminé"
    exit 0
}

# Capturer les signaux d'arrêt
trap cleanup SIGINT SIGTERM

# Vérifier les dépendances
echo "🔍 Vérification des dépendances..."

# Python et modules requis
python3 -c "import serial, modbus_tk" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Modules Python manquants. Installation..."
    pip3 install pyserial modbus-tk
fi

# Configuration des ports virtuels
echo ""
echo "🔧 Configuration des ports série virtuels..."
./test_environment/setup_virtual_ports.sh

if [ $? -ne 0 ]; then
    echo "❌ Échec de la configuration des ports virtuels"
    exit 1
fi

# Attendre que les ports soient prêts
sleep 2

# Démarrer le simulateur en arrière-plan
echo ""
echo "🚀 Démarrage du simulateur PZEM004T..."
python3 test_environment/pzem_simulator.py --voltage 230 --current 2.0 &
SIMULATOR_PID=$!

# Vérifier que le simulateur a démarré
sleep 3
if ! kill -0 $SIMULATOR_PID 2>/dev/null; then
    echo "❌ Échec du démarrage du simulateur"
    cleanup
    exit 1
fi

echo "✅ Simulateur démarré (PID: $SIMULATOR_PID)"

# Créer une copie de config pour le test si elle n'existe pas
if [ ! -f "config.json" ]; then
    echo ""
    echo "📝 Création du fichier de configuration de test..."
    cp test_environment/config_test.json config.json
    echo "✅ Configuration créée: config.json"
fi

echo ""
echo "🎯 === Environnement de test prêt ==="
echo ""
echo "📋 État du système:"
echo "   📡 Simulateur PZEM: ACTIF (PID: $SIMULATOR_PID)"
echo "   🔌 Port virtuel device: /tmp/pzem_test/pzem_device"
echo "   🖥️  Port virtuel host:   /tmp/pzem_test/pzem_host"
echo ""
echo "🚀 Pour tester le programme:"
echo "   python3 getPzemData.py"
echo ""
echo "💡 Conseils:"
echo "   - Le simulateur génère des données réalistes qui varient"
echo "   - Regardez les logs en mode DEBUG pour voir les échanges Modbus"
echo "   - Utilisez Ctrl+C pour arrêter proprement le test"
echo ""
echo "⏳ Test en cours... (Ctrl+C pour arrêter)"

# Attendre indéfiniment (ou jusqu'à Ctrl+C)
while true; do
    sleep 1
    # Vérifier que le simulateur tourne toujours
    if ! kill -0 $SIMULATOR_PID 2>/dev/null; then
        echo ""
        echo "⚠️  Le simulateur s'est arrêté de manière inattendue"
        cleanup
        exit 1
    fi
done
