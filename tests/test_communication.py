#!/usr/bin/python3
"""
Script de validation pour tester la communication avec le simulateur PZEM004T
"""

import serial
import struct
import time
import sys

def calculate_crc16(data):
    """Calcule le CRC16 Modbus"""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc

def test_pzem_communication(port_path="/tmp/pzem_test/pzem_host"):
    """Test basique de communication avec le simulateur"""
    try:
        print(f"🔌 Connexion au port: {port_path}")
        
        # Ouvrir le port série
        ser = serial.Serial(
            port=port_path,
            baudrate=9600,
            bytesize=8,
            parity='N',
            stopbits=1,
            timeout=2.0
        )
        
        print("✅ Port ouvert avec succès")
        
        # Construire une requête Modbus READ_INPUT_REGISTERS
        # Format: [device_id] [function] [start_addr_high] [start_addr_low] [count_high] [count_low] [crc_low] [crc_high]
        device_id = 1
        function = 0x04  # READ_INPUT_REGISTERS
        start_addr = 0
        count = 10
        
        request = bytearray([
            device_id,
            function,
            (start_addr >> 8) & 0xFF,
            start_addr & 0xFF,
            (count >> 8) & 0xFF,
            count & 0xFF
        ])
        
        # Calculer et ajouter le CRC
        crc = calculate_crc16(request)
        request.extend(struct.pack('<H', crc))  # Little endian
        
        print(f"📤 Envoi de la requête: {request.hex().upper()}")
        
        # Envoyer la requête
        ser.write(request)
        
        # Attendre et lire la réponse
        time.sleep(0.1)
        response = ser.read(100)  # Lire jusqu'à 100 bytes
        
        if len(response) > 0:
            print(f"📥 Réponse reçue: {response.hex().upper()}")
            
            if len(response) >= 25:  # 3 bytes header + 20 bytes data + 2 bytes CRC
                # Vérifier le CRC de la réponse
                received_crc = struct.unpack('<H', response[-2:])[0]
                calculated_crc = calculate_crc16(response[:-2])
                
                if received_crc == calculated_crc:
                    print("✅ CRC de la réponse correct")
                    
                    # Décoder les données
                    if response[0] == device_id and response[1] == 0x04:
                        byte_count = response[2]
                        if byte_count == 20:  # 10 registres * 2 bytes
                            registers = []
                            for i in range(10):
                                reg_offset = 3 + i * 2
                                reg_value = struct.unpack('>H', response[reg_offset:reg_offset+2])[0]
                                registers.append(reg_value)
                            
                            # Décoder selon le format PZEM004T
                            voltage = registers[0] / 10.0
                            current_ma = registers[1] + (registers[2] << 16)
                            current = current_ma / 1000.0
                            power_dw = registers[3] + (registers[4] << 16)
                            power = power_dw / 10.0
                            energy_wh = registers[5] + (registers[6] << 16)
                            energy = energy_wh / 1000.0
                            frequency = registers[7] / 10.0
                            power_factor = registers[8] / 100.0
                            
                            print("📊 === Données décodées ===")
                            print(f"   🔌 Tension:         {voltage:.1f} V")
                            print(f"   ⚡ Courant:         {current:.3f} A")
                            print(f"   💡 Puissance:       {power:.1f} W")
                            print(f"   🔋 Énergie:         {energy:.3f} kWh")
                            print(f"   📈 Fréquence:       {frequency:.1f} Hz")
                            print(f"   📊 Facteur puiss.:  {power_factor:.2f}")
                            print("✅ Test de communication réussi !")
                            return True
                        else:
                            print(f"❌ Nombre de bytes incorrect: {byte_count}")
                    else:
                        print(f"❌ En-tête de réponse incorrect: device={response[0]}, function={response[1]}")
                else:
                    print(f"❌ Erreur CRC: reçu {received_crc:04X}, calculé {calculated_crc:04X}")
            else:
                print(f"❌ Réponse trop courte: {len(response)} bytes")
        else:
            print("❌ Aucune réponse reçue (timeout)")
        
        ser.close()
        return False
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test de communication PZEM004T')
    parser.add_argument('--port', default='/tmp/pzem_test/pzem_host',
                       help='Port série à tester')
    
    args = parser.parse_args()
    
    print("🧪 === Test de Communication PZEM004T ===")
    print("")
    
    success = test_pzem_communication(args.port)
    
    print("")
    if success:
        print("🎉 Test réussi ! Le simulateur fonctionne correctement.")
        sys.exit(0)
    else:
        print("💥 Test échoué. Vérifiez que le simulateur est en cours d'exécution.")
        sys.exit(1)
