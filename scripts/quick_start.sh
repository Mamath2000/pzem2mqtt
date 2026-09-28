#!/bin/bash

# Script de démarrage rapide pour l'environnement de test PZEM2MQTT

echo "🚀 === Démarrage rapide PZEM2MQTT Test ==="
echo ""

# Vérifier si on est dans le bon répertoire
if [ ! -f "getPzemData.py" ]; then
    echo "❌ Erreur: Ce script doit être exécuté depuis le répertoire racine du projet"
    echo "   cd /path/to/pzem2mqtt && ./test_environment/quick_start.sh"
    exit 1
fi

echo "1️⃣ Configuration des ports virtuels..."
./test_environment/setup_virtual_ports.sh

echo ""
echo "2️⃣ Démarrage du simulateur en arrière-plan..."
python3 test_environment/pzem_simulator.py > /tmp/pzem_simulator.log 2>&1 &
SIMULATOR_PID=$!
echo "   Simulateur PID: $SIMULATOR_PID"
sleep 3

echo ""
echo "3️⃣ Test rapide de communication..."
python3 test_environment/test_communication.py --port "/tmp/pzem_test/pzem_host"

echo ""
echo "4️⃣ Configuration pour les tests..."
if [ -f "config.json" ] && [ ! -f "config.json.backup" ]; then
    cp config.json config.json.backup
    echo "   ✅ Configuration sauvegardée"
fi
cp test_environment/config_test.json config.json
echo "   ✅ Configuration de test activée"

echo ""
echo "✅ === Environnement prêt ==="
echo ""
echo "🎯 Maintenant vous pouvez :"
echo "   python3 getPzemData.py"
echo ""
echo "📊 Voir les logs du simulateur :"
echo "   tail -f /tmp/pzem_simulator.log"
echo ""
echo "🛑 Arrêter l'environnement :"
echo "   ./test_environment/stop_virtual_ports.sh"
echo "   kill $SIMULATOR_PID"
echo ""
echo "🔄 Restaurer la configuration originale :"
echo "   mv config.json.backup config.json"
