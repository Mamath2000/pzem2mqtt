#!/bin/bash

# Script pour arrêter les ports série virtuels

echo "🛑 Arrêt des ports série virtuels..."

# Arrêter le processus socat
if [ -f "/tmp/pzem_test/socat.pid" ]; then
    PID=$(cat /tmp/pzem_test/socat.pid)
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        echo "✅ Processus socat arrêté (PID: $PID)"
    else
        echo "⚠️  Le processus socat n'était pas en cours d'exécution"
    fi
    rm -f /tmp/pzem_test/socat.pid
else
    echo "⚠️  Fichier PID non trouvé, tentative d'arrêt par nom de processus..."
    pkill -f "socat.*pzem"
fi

# Nettoyer les liens symboliques
if [ -L "/tmp/pzem_test/pzem_device" ]; then
    rm -f /tmp/pzem_test/pzem_device
    echo "🧹 Lien pzem_device supprimé"
fi

if [ -L "/tmp/pzem_test/pzem_host" ]; then
    rm -f /tmp/pzem_test/pzem_host
    echo "🧹 Lien pzem_host supprimé"
fi

echo "✅ Nettoyage terminé"
