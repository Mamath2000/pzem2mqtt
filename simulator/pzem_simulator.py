#!/usr/bin/python3
"""
Simulateur PZEM004T v3.0 - Répond aux requêtes Modbus RTU

Ce simulateur écoute sur un port série virtuel et répond aux requêtes Modbus
avec des données simulées qui correspondent au format du PZEM004T.

Format des registres PZEM004T (READ_INPUT_REGISTERS, addr 0, count 10):
- Registre 0: Tension * 10 (ex: 2300 = 230.0V)
- Registre 1-2: Courant en mA (32 bits, little endian)
- Registre 3-4: Puissance * 10 (32 bits, little endian)  
- Registre 5-6: Énergie en Wh (32 bits, little endian)
- Registre 7: Fréquence * 10 (ex: 500 = 50.0Hz)
- Registre 8: Facteur de puissance * 100 (ex: 85 = 0.85)
- Registre 9: Alarme (non utilisé généralement)
"""

import serial
import struct
import threading
import time
import random
import math
import logging
from datetime import datetime

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [SIMULATOR] %(levelname)-8s %(message)s'
)
logger = logging.getLogger(__name__)

class PZEMSimulator:
    def __init__(self, port_path="/tmp/pzem_test/pzem_device"):
        self.port_path = port_path
        self.serial_port = None
        self.running = False
        
        # Valeurs de base pour la simulation (peuvent être variées)
        self.base_voltage = 230.0     # Volts
        self.base_current = 1.5       # Ampères  
        self.base_frequency = 50.0    # Hertz
        self.base_power_factor = 0.85 # Facteur de puissance
        self.energy_counter = 12345   # Compteur d'énergie en Wh (s'incrémente)
        
        # Paramètres de variation pour rendre la simulation réaliste
        self.voltage_variation = 5.0   # +/- volts
        self.current_variation = 0.3   # +/- ampères
        self.freq_variation = 0.5      # +/- Hz
        
        # Heure de démarrage pour calculer l'accumulation d'énergie
        self.start_time = time.time()
        
    def calculate_crc16(self, data):
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
        
    def generate_realistic_values(self):
        """Génère des valeurs réalistes qui varient légèrement"""
        # Utiliser le temps pour créer des variations cycliques
        t = time.time() - self.start_time
        
        # Tension avec légère variation sinusoïdale
        voltage = self.base_voltage + math.sin(t * 0.1) * self.voltage_variation
        voltage = max(200.0, min(250.0, voltage))  # Limiter entre 200V et 250V
        
        # Courant avec variation aléatoire et cyclique
        current = self.base_current + (random.random() - 0.5) * self.current_variation
        current += math.sin(t * 0.05) * 0.2  # Variation lente
        current = max(0.0, current)  # Pas de courant négatif
        
        # Fréquence stable avec micro-variations
        frequency = self.base_frequency + (random.random() - 0.5) * self.freq_variation
        frequency = max(49.0, min(51.0, frequency))  # Entre 49 et 51 Hz
        
        # Facteur de puissance stable
        power_factor = self.base_power_factor + (random.random() - 0.5) * 0.05
        power_factor = max(0.1, min(1.0, power_factor))
        
        # Calcul de la puissance
        power = voltage * current * power_factor
        
        # Incrémentation de l'énergie (approximative)
        energy_increment = power * (time.time() - getattr(self, 'last_energy_update', self.start_time)) / 3600.0
        self.energy_counter += int(energy_increment)
        self.last_energy_update = time.time()
        
        return {
            'voltage': voltage,
            'current': current,
            'power': power,
            'energy_wh': self.energy_counter,
            'frequency': frequency,
            'power_factor': power_factor
        }
    
    def create_modbus_response(self, values):
        """Crée une réponse Modbus avec les valeurs données"""
        # Format de réponse Modbus: [device_id] [function] [byte_count] [data...] [crc_low] [crc_high]
        
        # Convertir les valeurs au format PZEM
        voltage_reg = int(values['voltage'] * 10)  # ex: 2300 pour 230.0V
        current_ma = int(values['current'] * 1000)  # en milliampères
        power_dw = int(values['power'] * 10)  # en déci-watts
        energy_wh = int(values['energy_wh'])  # en Wh
        frequency_dh = int(values['frequency'] * 10)  # en déci-Hz
        power_factor_percent = int(values['power_factor'] * 100)  # en pourcentage
        
        # Construire les registres (10 registres de 16 bits chacun)
        registers = [
            voltage_reg,                    # Registre 0
            current_ma & 0xFFFF,           # Registre 1 (partie basse du courant)
            (current_ma >> 16) & 0xFFFF,   # Registre 2 (partie haute du courant)
            power_dw & 0xFFFF,             # Registre 3 (partie basse de la puissance)
            (power_dw >> 16) & 0xFFFF,     # Registre 4 (partie haute de la puissance)
            energy_wh & 0xFFFF,            # Registre 5 (partie basse de l'énergie)
            (energy_wh >> 16) & 0xFFFF,    # Registre 6 (partie haute de l'énergie)
            frequency_dh,                   # Registre 7
            power_factor_percent,           # Registre 8
            0x0000                          # Registre 9 (alarme)
        ]
        
        return registers
    
    def handle_modbus_request(self, request_data):
        """Traite une requête Modbus et retourne la réponse"""
        if len(request_data) < 4:
            logger.warning("Requête Modbus trop courte")
            return None
            
        device_id = request_data[0]
        function_code = request_data[1]
        
        # Vérifier le CRC de la requête
        received_crc = struct.unpack('<H', request_data[-2:])[0]  # Little endian
        calculated_crc = self.calculate_crc16(request_data[:-2])
        
        if received_crc != calculated_crc:
            logger.warning(f"Erreur CRC dans la requête: reçu {received_crc:04X}, calculé {calculated_crc:04X}")
            return None
        
        # Traiter seulement READ_INPUT_REGISTERS (0x04)
        if function_code == 0x04:
            start_addr = struct.unpack('>H', request_data[2:4])[0]  # Big endian
            reg_count = struct.unpack('>H', request_data[4:6])[0]   # Big endian
            
            logger.debug(f"Requête INPUT_REGISTERS: device_id={device_id}, start={start_addr}, count={reg_count}")
            
            if start_addr == 0 and reg_count == 10:
                # Générer des valeurs réalistes
                values = self.generate_realistic_values()
                registers = self.create_modbus_response(values)
                
                # Construire la réponse Modbus
                response = bytearray()
                response.append(device_id)        # Device ID
                response.append(0x04)             # Function code
                response.append(reg_count * 2)    # Byte count (20 bytes pour 10 registres)
                
                # Ajouter les registres (big endian)
                for reg in registers:
                    response.extend(struct.pack('>H', reg & 0xFFFF))
                
                # Calculer et ajouter le CRC
                crc = self.calculate_crc16(response)
                response.extend(struct.pack('<H', crc))  # Little endian
                
                logger.info(f"Réponse générée pour device_id {device_id}: "
                          f"V={values['voltage']:.1f}V, I={values['current']:.3f}A, "
                          f"P={values['power']:.1f}W, E={values['energy_wh']}Wh")
                
                return bytes(response)
            else:
                logger.warning(f"Requête non supportée: start_addr={start_addr}, count={reg_count}")
        else:
            logger.warning(f"Code de fonction non supporté: {function_code}")
        
        return None
    
    def start_simulation(self):
        """Démarre le simulateur"""
        try:
            logger.info(f"Ouverture du port série: {self.port_path}")
            self.serial_port = serial.Serial(
                port=self.port_path,
                baudrate=9600,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=1.0
            )
            
            logger.info("✅ Simulateur PZEM004T démarré et en attente de requêtes...")
            logger.info(f"   📊 Valeurs de base: {self.base_voltage}V, {self.base_current}A, {self.base_frequency}Hz")
            
            self.running = True
            request_count = 0
            
            while self.running:
                try:
                    # Lire les données disponibles
                    if self.serial_port.in_waiting > 0:
                        # Lire jusqu'à 8 bytes (taille typique d'une requête Modbus)
                        request_data = self.serial_port.read(8)
                        
                        if len(request_data) >= 6:  # Minimum pour une requête Modbus valide
                            request_count += 1
                            logger.debug(f"Requête #{request_count} reçue: {request_data.hex().upper()}")
                            
                            response = self.handle_modbus_request(request_data)
                            if response:
                                self.serial_port.write(response)
                                logger.debug(f"Réponse envoyée: {response.hex().upper()}")
                            else:
                                logger.warning("Aucune réponse générée pour cette requête")
                    
                    time.sleep(0.01)  # Petit délai pour éviter une boucle trop rapide
                    
                except serial.SerialException as e:
                    logger.error(f"Erreur série: {e}")
                    break
                except Exception as e:
                    logger.error(f"Erreur inattendue: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Erreur lors de l'ouverture du port série: {e}")
        finally:
            if self.serial_port:
                self.serial_port.close()
                logger.info("Port série fermé")
    
    def stop_simulation(self):
        """Arrête le simulateur"""
        self.running = False
        logger.info("Arrêt du simulateur demandé")

def main():
    import argparse
    import signal
    import sys
    
    parser = argparse.ArgumentParser(description='Simulateur PZEM004T')
    parser.add_argument('--port', default='/tmp/pzem_test/pzem_device',
                       help='Chemin vers le port série virtuel')
    parser.add_argument('--voltage', type=float, default=230.0,
                       help='Tension de base (V)')
    parser.add_argument('--current', type=float, default=1.5,
                       help='Courant de base (A)')
    parser.add_argument('--debug', action='store_true',
                       help='Mode debug verbose')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Créer le simulateur
    simulator = PZEMSimulator(args.port)
    simulator.base_voltage = args.voltage
    simulator.base_current = args.current
    
    # Gestionnaire de signal pour arrêt propre
    def signal_handler(signum, frame):
        logger.info("Signal d'arrêt reçu")
        simulator.stop_simulation()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        simulator.start_simulation()
    except KeyboardInterrupt:
        logger.info("Arrêt par Ctrl+C")
    except Exception as e:
        logger.error(f"Erreur fatale: {e}")

if __name__ == "__main__":
    main()
