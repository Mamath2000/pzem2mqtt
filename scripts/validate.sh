#!/bin/bash

echo "=== Validation de l'installation PZEM2MQTT ==="

# Vérification des fichiers essentiels
echo "1. Vérification des fichiers essentiels..."
required_files=("getPzemData.py" "config.json" "requirements.txt" "pzem2mqtt.service")
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✓ $file"
    else
        echo "   ✗ $file manquant"
    fi
done

# Vérification de la configuration JSON
echo ""
echo "2. Validation du fichier de configuration..."
if python3 -c "import json; json.load(open('config.json'))" 2>/dev/null; then
    echo "   ✓ config.json est valide"
    
    # Affichage de la configuration actuelle
    echo ""
    echo "3. Configuration actuelle:"
    python3 -c "
import json
with open('config.json', 'r') as f:
    config = json.load(f)
print(f'   MQTT Host: {config[\"mqtt\"][\"host\"]}:{config[\"mqtt\"][\"port\"]}')
print(f'   Port série: {config[\"serial\"][\"port\"]}')
print(f'   Niveau de log: {config[\"general\"].get(\"log_level\", \"INFO\")}')
print(f'   Capteurs configurés: {len(config[\"sensors\"])}')
for i, sensor in enumerate(config['sensors']):
    status = 'activé' if sensor.get('enabled', True) else 'désactivé'
    print(f'     - {sensor[\"name\"]} (ID: {sensor[\"device_id\"]}) - {status}')
"
else
    echo "   ✗ config.json invalide"
fi

# Vérification des dépendances Python
echo ""
echo "4. Vérification des dépendances Python..."
dependencies=("modbus_tk" "serial" "paho.mqtt.client" "schedule")
for dep in "${dependencies[@]}"; do
    if python3 -c "import $dep" 2>/dev/null; then
        echo "   ✓ $dep"
    else
        echo "   ✗ $dep manquant"
    fi
done

# Vérification du service systemd
echo ""
echo "5. Vérification du service systemd..."
if [ -f "/etc/systemd/system/pzem2mqtt.service" ]; then
    echo "   ✓ Service installé"
    if systemctl is-enabled pzem2mqtt.service >/dev/null 2>&1; then
        echo "   ✓ Service activé"
    else
        echo "   ✗ Service non activé"
    fi
    
    if systemctl is-active pzem2mqtt.service >/dev/null 2>&1; then
        echo "   ✓ Service en cours d'exécution"
    else
        echo "   ⚠ Service arrêté"
    fi
else
    echo "   ✗ Service non installé"
fi

echo ""
echo "=== Fin de la validation ==="
