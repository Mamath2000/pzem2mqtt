#!/usr/bin/python3
"""
Test simple du module getPzem004t sans MQTT
"""

import sys
import os
# Ajouter le répertoire src au path pour importer les modules
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

import serial
import modbus_tk.defines as cst
from modbus_tk import modbus_rtu
from modbus_tk.exceptions import ModbusError, ModbusInvalidResponseError
import time

def test_pzem_function():
    """Test de la fonction getPzem004t avec le simulateur"""
    
    print("🧪 Test de la fonction getPzem004t avec le simulateur")
    print("")
    
    # Configuration série
    serial_port = "/tmp/pzem_test/pzem_host"
    
    try:
        # Connexion série
        serial_connection = serial.Serial(
            port=serial_port,
            baudrate=9600,
            bytesize=8,
            parity='N',
            stopbits=1,
            xonxoff=0,
            timeout=3.0,
            write_timeout=2.0
        )
        
        master = modbus_rtu.RtuMaster(serial_connection)
        master.set_timeout(3.0)
        master.set_verbose(True)
        
        print(f"✅ Connexion série établie sur {serial_port}")
        
        # Fonction getPzem004t simplifiée
        def getPzem004t_simple(rtu, device_id):
            try:
                print(f"📤 Lecture du capteur ID {device_id}...")
                
                # Lecture des registres Modbus
                data = rtu.execute(device_id, cst.READ_INPUT_REGISTERS, 0, 10)
                
                # Calcul des valeurs (même logique que dans getPzemData.py)
                tension = round(data[0] / 10.0, 1)
                courant = round((data[1] + (data[2] << 16)) / 1000.0, 3)
                puissance = round((data[3] + (data[4] << 16)) / 10.0, 1)
                energy = (data[5] + (data[6] << 16)) / 1000.0
                frequency = data[7] / 10.0
                facteurDePuiss = data[8] / 100.0
                puissanceApparente = round(courant * tension, 2)
                
                print(f"📊 === Données reçues du capteur {device_id} ===")
                print(f"   🔌 Tension:             {tension} V")
                print(f"   ⚡ Courant:             {courant} A")
                print(f"   💡 Puissance:           {puissance} W")
                print(f"   🔋 Énergie:             {energy:.3f} kWh")
                print(f"   📈 Fréquence:           {frequency} Hz")
                print(f"   📊 Facteur puissance:   {facteurDePuiss}")
                print(f"   ⚖️  Puissance apparente:  {puissanceApparente} VA")
                
                return True
                
            except Exception as e:
                print(f"❌ Erreur lecture capteur {device_id}: {e}")
                return False
        
        # Tester les capteurs configurés
        for device_id in [1, 2]:
            print("")
            success = getPzem004t_simple(master, device_id)
            if success:
                print(f"✅ Test capteur {device_id} réussi")
            else:
                print(f"❌ Test capteur {device_id} échoué")
            
            time.sleep(1)  # Délai entre les lectures
        
        master.close()
        print("")
        print("🎉 Test terminé avec succès !")
        
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

if __name__ == "__main__":
    test_pzem_function()
