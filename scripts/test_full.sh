#!/bin/bash

# Script de test automatisé pour PZEM2MQTT avec simulateur

set -e  # Arrêter en cas d'erreur

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🧪 === Test Automatisé PZEM2MQTT ==="
echo "📁 Répertoire du projet: $PROJECT_DIR"
echo ""

# Variables globales
SIMULATOR_PID=""
SOCAT_PID=""

# Fonction de nettoyage
cleanup() {
    echo ""
    echo "🧹 Nettoyage en cours..."
    
    if [ ! -z "$SIMULATOR_PID" ] && kill -0 "$SIMULATOR_PID" 2>/dev/null; then
        kill "$SIMULATOR_PID" 2>/dev/null
        echo "   ✅ Simulateur arrêté (PID: $SIMULATOR_PID)"
    fi
    
    # Arrêter les ports virtuels
    "$SCRIPT_DIR/stop_virtual_ports.sh" 2>/dev/null || true
    
    echo "🏁 Nettoyage terminé"
}

# Gestionnaire de signaux
trap cleanup EXIT SIGINT SIGTERM

# Étape 1: Vérification des dépendances
echo "🔍 Vérification des dépendances..."

MISSING_DEPS=0

# Vérifier socat
if ! command -v socat &> /dev/null; then
    echo "❌ socat non trouvé"
    MISSING_DEPS=1
fi

# Vérifier les modules Python
python3 -c "import serial, modbus_tk, paho.mqtt.client, schedule, pytz" 2>/dev/null || {
    echo "❌ Modules Python manquants"
    MISSING_DEPS=1
}

if [ $MISSING_DEPS -eq 1 ]; then
    echo ""
    echo "🔧 Installation des dépendances manquantes..."
    
    # Installer socat si nécessaire
    if ! command -v socat &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y socat
    fi
    
    # Installer les modules Python si nécessaire
    pip3 install --break-system-packages pyserial modbus-tk paho-mqtt schedule pytz 2>/dev/null || {
        echo "⚠️ Erreur d'installation des modules Python. Continuons..."
    }
fi

echo "✅ Dépendances vérifiées"

# Étape 2: Configuration des ports virtuels
echo ""
echo "🔧 Configuration des ports série virtuels..."
"$SCRIPT_DIR/setup_virtual_ports.sh"

if [ $? -ne 0 ]; then
    echo "❌ Échec de la configuration des ports virtuels"
    exit 1
fi

# Attendre que les ports soient prêts
sleep 2

# Étape 3: Démarrage du simulateur
echo ""
echo "🚀 Démarrage du simulateur PZEM004T..."
python3 "$PROJECT_DIR/simulator/pzem_simulator.py" --voltage 230 --current 2.0 > /tmp/pzem_simulator.log 2>&1 &
SIMULATOR_PID=$!

# Vérifier que le simulateur a démarré
sleep 3
if ! kill -0 "$SIMULATOR_PID" 2>/dev/null; then
    echo "❌ Échec du démarrage du simulateur"
    echo "📋 Logs du simulateur:"
    cat /tmp/pzem_simulator.log
    exit 1
fi

echo "✅ Simulateur démarré (PID: $SIMULATOR_PID)"

# Étape 4: Test de communication basique
echo ""
echo "🔗 Test de communication basique..."
python3 "$PROJECT_DIR/tests/test_communication.py" --port "/tmp/pzem_test/pzem_host"

if [ $? -ne 0 ]; then
    echo "❌ Test de communication échoué"
    exit 1
fi

# Étape 5: Test des fonctions PZEM
echo ""
echo "🧪 Test des fonctions PZEM..."
python3 "$PROJECT_DIR/tests/test_pzem_function.py"

if [ $? -ne 0 ]; then
    echo "❌ Test des fonctions PZEM échoué"
    exit 1
fi

# Étape 6: Sauvegarde de la configuration actuelle et création de la config de test
echo ""
echo "📝 Configuration du fichier config.json pour les tests..."

if [ -f "$PROJECT_DIR/config.json" ] && [ ! -f "$PROJECT_DIR/config.json.backup" ]; then
    cp "$PROJECT_DIR/config.json" "$PROJECT_DIR/config.json.backup"
    echo "✅ Configuration actuelle sauvegardée dans config.json.backup"
fi

cp "$PROJECT_DIR/config/config.test.json" "$PROJECT_DIR/config/config.json"
echo "✅ Configuration de test appliquée"

# Étape 7: Informations finales
echo ""
echo "🎯 === Environnement de test prêt ==="
echo ""
echo "📊 État du système:"
echo "   📡 Simulateur PZEM: ACTIF (PID: $SIMULATOR_PID)"
echo "   🔌 Port device:     /tmp/pzem_test/pzem_device"
echo "   🖥️  Port host:       /tmp/pzem_test/pzem_host"
echo "   📁 Config backup:   config.json.backup"
echo "   📋 Logs simulateur: /tmp/pzem_simulator.log"
echo ""
echo "🚀 Pour tester le programme complet:"
echo "   cd $PROJECT_DIR"
echo "   make run"
echo ""
echo "📈 Pour voir les logs du simulateur en temps réel:"
echo "   tail -f /tmp/pzem_simulator.log"
echo ""
echo "💡 Conseils:"
echo "   - Le simulateur génère des données qui varient légèrement"
echo "   - Configurez votre broker MQTT dans config.json si nécessaire"
echo "   - Les données sont publiées sur 'pzem2mqtt/test/test_sensor_X_energy'"
echo ""
echo "🛑 Pour arrêter l'environnement de test:"
echo "   Ctrl+C ou $SCRIPT_DIR/stop_virtual_ports.sh"
echo ""
echo "⏳ L'environnement reste actif... Appuyez sur Ctrl+C pour arrêter"

# Attendre indéfiniment (ou jusqu'à Ctrl+C)
while true; do
    sleep 5
    
    # Vérifier que le simulateur tourne toujours
    if ! kill -0 "$SIMULATOR_PID" 2>/dev/null; then
        echo ""
        echo "⚠️ Le simulateur s'est arrêté de manière inattendue"
        echo "📋 Derniers logs:"
        tail -20 /tmp/pzem_simulator.log
        exit 1
    fi
done
