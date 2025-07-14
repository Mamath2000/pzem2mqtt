#!/usr/bin/python3

# Reading PZEM-004t power sensor (new version v3.0) through Modbus-RTU protocol over TTL UART
# Run as:
# python3 pzem_004t.py

# To install dependencies:
# pip install modbus-tk
# pip install pyserial

import serial
import modbus_tk.defines as cst
from modbus_tk import modbus_rtu
from modbus_tk.exceptions import ModbusError, ModbusInvalidResponseError
import schedule
import paho.mqtt.client as mqtt
import logging
import json
import time
import os

from datetime import datetime
from pytz import timezone


# =================== Configuration Loading ===============================
def load_config():
    """Charge la configuration depuis le fichier config.json"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Fichier de configuration {config_path} non trouvé")
        raise
    except json.JSONDecodeError as e:
        print(f"Erreur lors du parsing du fichier de configuration: {e}")
        raise

# Chargement de la configuration
config = load_config()

# Configuration du logging avec le niveau depuis la configuration
log_level = getattr(logging, config['general'].get('log_level', 'INFO').upper())
logging.basicConfig(level=log_level, format='   %(asctime)s %(levelname)-8s %(message)s')
logger = logging.getLogger()

# Variables globales depuis la configuration
mqtt_host = config['mqtt']['host']
mqtt_port = config['mqtt']['port']
auto_discovery = config['mqtt']['auto_discovery']
discovery_topic = config['mqtt']['discovery_topic']
serial_port = config['serial']['port']
base_topic = config['mqtt']['base_topic']
local_tz = config['general']['local_tz']
poll_interval = config['general']['poll_interval']
lwt_topic = base_topic + "/lwt"
monitoring_topic = base_topic + "/monitoring"

# Statistiques d'erreurs pour le monitoring
error_stats = {
    'total_reads': 0,
    'crc_errors': 0,
    'timeout_errors': 0,
    'other_errors': 0,
    'consecutive_errors': 0,
    'last_successful_read': None,
    'last_monitoring_publish': None,
    'session_start': datetime.now(),
    'last_reads_by_sensor': {}  # Stockage des dernières lectures par capteur
}
# ==================================================================


def on_connect(client, userdata, flags, reason_code, properties=None):
    """ Connection MQTT handler"""

    global lwt_topic
    logger.info("Connected to MQTT server with result code " + str(reason_code))

    client.publish(lwt_topic, "online", qos=1, retain=True)

def getPzem004t(rtu, id, max_retries=3):
    """
    Lecture des données PZEM avec gestion des erreurs CRC et retry automatique
    """
    global error_stats
    
    for attempt in range(max_retries):
        try:
            error_stats['total_reads'] += 1
            
            # Petit délai avant chaque tentative pour stabiliser la communication
            time.sleep(0.1)
            
            # Lecture des registres Modbus
            data = rtu.execute(id, cst.READ_INPUT_REGISTERS, 0, 10)

            # Calcul des valeurs
            tension = round(data[0] / 10.0, 1)                        # [V]
            courant = round((data[1] + (data[2] << 16)) / 1000.0, 3)  # [A]
            courant_ma = round(data[1] + (data[2] << 16), 0)          # [mA]
            puissance = round((data[3] + (data[4] << 16)) / 10.0, 1)  # [W]
            energy = (data[5] + (data[6] << 16)) / 1000.0             # [kWh]
            index = (data[5] + (data[6] << 16))                       # [Wh]
            frequency = data[7] / 10.0                                # [Hz]
            facteurDePuiss = data[8] / 100.0                          # [%]
            puissanceApparente = round(courant * tension, 2)          # [VA]

            logger.debug("Index [Wh] : {0}".format(index))
            logger.debug("Tension [V] : {0}".format(tension))
            logger.debug("Courant [A] : {0}".format(courant))
            logger.debug("Courant [mA] : {0}".format(courant_ma))
            logger.debug("Puissance [W] : {0}".format(puissance))
            logger.debug("Energy [kWh] : {0}".format(energy))
            logger.debug("Frequency [Hz] : {0}".format(frequency))
            logger.debug("Facteur de Puiss. [%] : {0}".format(facteurDePuiss))
            logger.debug("Puissance Apparente [VA] : {0}".format(puissanceApparente))

            # Réussite - reset du compteur d'erreurs consécutives
            error_stats['consecutive_errors'] = 0
            error_stats['last_successful_read'] = datetime.now()
            
            # Timestamp de la lecture
            reading_timestamp = datetime.now()
            reading_timestamp_local = reading_timestamp.replace(tzinfo=timezone(local_tz))
            
            # Stockage de la dernière lecture pour ce capteur
            error_stats['last_reads_by_sensor'][id] = {
                'timestamp': reading_timestamp,
                'timestamp_local': reading_timestamp_local,
                'success': True
            }
            
            logger.info("Reading PZEM004T ok. Sensor n° {0} (attempt {1}/{2})".format(id, attempt + 1, max_retries))
            
            jsondata = {
                "current": float(courant),
                "energy": float(energy),
                "power": round(float(puissance), 1),
                "voltage": float(tension),
                "facteur_de_puiss": float(facteurDePuiss),
                "frequency": float(frequency),
                "apparent_power": float(puissanceApparente),
                "timestamp": reading_timestamp.isoformat(),
                "timestamp_local": reading_timestamp_local.isoformat(),
                "last_read": reading_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "last_read_local": reading_timestamp_local.strftime("%Y-%m-%d %H:%M:%S %Z")
            }
            return jsondata

        except ModbusInvalidResponseError as e:
            error_stats['crc_errors'] += 1
            error_stats['consecutive_errors'] += 1
            
            # Enregistrement de l'échec pour ce capteur
            error_stats['last_reads_by_sensor'][id] = {
                'timestamp': datetime.now(),
                'timestamp_local': datetime.now().replace(tzinfo=timezone(local_tz)),
                'success': False,
                'error_type': 'crc_error'
            }
            
            logger.warning(f"Erreur CRC capteur {id}, tentative {attempt + 1}/{max_retries}: {str(e)}")
            
            if attempt < max_retries - 1:
                # Délai progressif entre les tentatives
                delay = 0.5 * (attempt + 1)
                logger.debug(f"Attente de {delay}s avant la prochaine tentative")
                time.sleep(delay)
            
        except Exception as e:
            if "timeout" in str(e).lower():
                error_stats['timeout_errors'] += 1
                error_type = 'timeout_error'
            else:
                error_stats['other_errors'] += 1
                error_type = 'other_error'
            
            error_stats['consecutive_errors'] += 1
            
            # Enregistrement de l'échec pour ce capteur
            error_stats['last_reads_by_sensor'][id] = {
                'timestamp': datetime.now(),
                'timestamp_local': datetime.now().replace(tzinfo=timezone(local_tz)),
                'success': False,
                'error_type': error_type
            }
            
            logger.warning(f"Erreur lecture capteur {id}, tentative {attempt + 1}/{max_retries}: {str(e)}")
            
            if attempt < max_retries - 1:
                delay = 0.5 * (attempt + 1)
                time.sleep(delay)

    # Toutes les tentatives ont échoué
    logger.error(f"Échec lecture capteur {id} après {max_retries} tentatives. Stats: CRC={error_stats['crc_errors']}, Timeout={error_stats['timeout_errors']}, Autres={error_stats['other_errors']}")
    return None

def process(client, rtu):
    """Traite tous les capteurs configurés avec gestion améliorée des erreurs"""
    global base_topic, config, error_stats

    # Vérification si trop d'erreurs consécutives - reinitialisation de la connexion série
    if error_stats['consecutive_errors'] >= 10:
        logger.warning(f"Trop d'erreurs consécutives ({error_stats['consecutive_errors']}), tentative de réinitialisation de la connexion série")
        try:
            rtu.close()
            time.sleep(2)
            rtu.open()
            error_stats['consecutive_errors'] = 0
            logger.info("Connexion série réinitialisée avec succès")
        except Exception as e:
            logger.error(f"Échec de la réinitialisation de la connexion série: {e}")

    for i, sensor in enumerate(config['sensors']):
        if not sensor.get('enabled', True):
            logger.debug(f"Capteur {sensor['name']} désactivé, passage au suivant")
            continue

        logger.debug(f"Lecture du capteur {sensor['name']} (ID: {sensor['device_id']}) - {i+1}/{len([s for s in config['sensors'] if s.get('enabled', True)])}")
        
        # Lecture avec retry automatique
        payload = getPzem004t(rtu, sensor['device_id'])
        
        # Délai entre chaque lecture pour éviter les collisions sur le bus
        time.sleep(0.5)
        
        if payload:
            component_id = sensor['unique_id']
            topic = f"{base_topic}/{component_id}"
            client.publish(topic, json.dumps(payload), qos=0, retain=True)
            logger.info(f"Données publiées pour {sensor['name']} sur {topic}")
        else:
            logger.warning(f"Échec de lecture du capteur {sensor['name']} (ID: {sensor['device_id']})")

        # Délai plus long entre chaque capteur pour stabiliser la communication
        if i < len([s for s in config['sensors'] if s.get('enabled', True)]) - 1:  # Pas de délai après le dernier capteur
            time.sleep(1.5)
    
    # Publication des statistiques de monitoring toutes les 10 lectures ou en cas de problème
    should_publish_monitoring = (
        error_stats['total_reads'] % 30 == 0 or  # Toutes les 30 lectures
        error_stats['consecutive_errors'] >= 5 or  # En cas de problèmes
        error_stats['last_monitoring_publish'] is None or  # Premier envoi
        (datetime.now() - error_stats['last_monitoring_publish']).total_seconds() > 300  # Toutes les 5 minutes minimum
    )
    
    if should_publish_monitoring and error_stats['total_reads'] > 0:
        publish_monitoring_stats(client)
    
    # Log des statistiques d'erreurs périodiquement (moins fréquent maintenant)
    if error_stats['total_reads'] % 100 == 0 and error_stats['total_reads'] > 0:
        success_rate = round((error_stats['total_reads'] - error_stats['crc_errors'] - error_stats['timeout_errors'] - error_stats['other_errors']) / error_stats['total_reads'] * 100, 2)
        logger.info(f"Statistiques locales: {error_stats['total_reads']} lectures totales, {success_rate}% de succès, CRC errors: {error_stats['crc_errors']}, Timeouts: {error_stats['timeout_errors']}")

def sendDiscoveryConfig(client, sensor):
    """Envoie la configuration de découverte pour un capteur"""
    unique_id = f"{sensor['unique_id']}_energy"
    topic_state = f"{base_topic}/{sensor['unique_id']}"
    topic_config = f"{discovery_topic}/sensor/{sensor['unique_id']}/energy/config"

    payload = {
        "name": "energy",
        "state_topic": topic_state,
        "value_template": "{{ value_json.energy }}",
        "unit_of_measurement": "kWh",
        "device_class": "energy",
        "unique_id": unique_id,
        "object_id": unique_id,
        "json_attributes_topic": topic_state,
        "device": {
            "identifiers": [unique_id],
            "name": sensor['name'],
            "manufacturer": "Mamath",
            "model": "PZEM-004T v3.0"
        },
        "origin": {
            "name": "pzem2mqtt",
            "url": "https://github.com/Mamath2000/pzem2mqtt.git"
        },
    }

    client.publish(topic_config, json.dumps(payload), qos=0, retain=True)
    logger.info(f"Configuration de découverte envoyée pour {sensor['name']}")

def setup_discovery_configs(client):
    """Configure la découverte automatique pour tous les capteurs activés"""
    if not auto_discovery:
        logger.info("Auto-découverte désactivée")
        return

    for sensor in config['sensors']:
        if sensor.get('enabled', True):
            sendDiscoveryConfig(client, sensor)

# def setup_monitoring_discovery(client):
#     """Configure la découverte automatique pour le monitoring"""
#     if not auto_discovery:
#         return
    
#     monitoring_config = {
#         "name": "PZEM2MQTT Monitoring",
#         "state_topic": monitoring_topic,
#         "value_template": "{{ value_json.success_rate_percent }}",
#         "unit_of_measurement": "%",
#         "icon": "mdi:chart-line",
#         "unique_id": "pzem2mqtt_monitoring",
#         "object_id": "pzem2mqtt_monitoring",
#         "json_attributes_topic": monitoring_topic,
#         "device": {
#             "identifiers": ["pzem2mqtt_system"],
#             "name": "PZEM2MQTT System",
#             "manufacturer": "Mamath",
#             "model": "PZEM2MQTT Monitor",
#             "sw_version": "1.1"
#         },
#         "origin": {
#             "name": "pzem2mqtt",
#             "url": "https://github.com/Mamath2000/pzem2mqtt.git"
#         }
#     }
    
#     monitoring_discovery_topic = f"{discovery_topic}/sensor/pzem2mqtt_system/monitoring/config"
#     client.publish(monitoring_discovery_topic, json.dumps(monitoring_config), qos=0, retain=True)
#     logger.info("Configuration de découverte pour le monitoring envoyée")

def publish_monitoring_stats(client):
    """Publie les statistiques de monitoring sur MQTT"""
    global error_stats, monitoring_topic
    
    now = datetime.now()
    session_duration = (now - error_stats['session_start']).total_seconds()
    
    # Calcul du taux de succès
    total_errors = error_stats['crc_errors'] + error_stats['timeout_errors'] + error_stats['other_errors']
    success_rate = round((error_stats['total_reads'] - total_errors) / error_stats['total_reads'] * 100, 2) if error_stats['total_reads'] > 0 else 0
    
    # Calcul du taux de lecture par minute
    reads_per_minute = round(error_stats['total_reads'] / (session_duration / 60), 2) if session_duration > 0 else 0
    
    # Préparation des informations par capteur
    sensors_status = {}
    for sensor in config['sensors']:
        sensor_id = sensor['device_id']
        if sensor_id in error_stats['last_reads_by_sensor']:
            last_read_info = error_stats['last_reads_by_sensor'][sensor_id]
            sensors_status[f"sensor_{sensor_id}"] = {
                "name": sensor['name'],
                "last_read_timestamp": last_read_info['timestamp'].isoformat(),
                "last_read_local": last_read_info['timestamp_local'].strftime("%Y-%m-%d %H:%M:%S %Z"),
                "last_read_success": last_read_info['success'],
                "error_type": last_read_info.get('error_type', None) if not last_read_info['success'] else None,
                "enabled": sensor.get('enabled', True)
            }
        else:
            sensors_status[f"sensor_{sensor_id}"] = {
                "name": sensor['name'],
                "last_read_timestamp": None,
                "last_read_local": "Jamais lu",
                "last_read_success": None,
                "error_type": None,
                "enabled": sensor.get('enabled', True)
            }
    
    monitoring_data = {
        "timestamp": now.isoformat(),
        "session_duration_minutes": round(session_duration / 60, 1),
        "total_reads": error_stats['total_reads'],
        "success_rate_percent": success_rate,
        "reads_per_minute": reads_per_minute,
        "errors": {
            "crc_errors": error_stats['crc_errors'],
            "timeout_errors": error_stats['timeout_errors'],
            "other_errors": error_stats['other_errors'],
            "consecutive_errors": error_stats['consecutive_errors']
        },
        "last_successful_read": error_stats['last_successful_read'].isoformat() if error_stats['last_successful_read'] else None,
        "health_status": "healthy" if error_stats['consecutive_errors'] < 5 else "degraded" if error_stats['consecutive_errors'] < 10 else "critical",
        "enabled_sensors": len([s for s in config['sensors'] if s.get('enabled', True)]),
        "total_sensors": len(config['sensors']),
        "sensors_status": sensors_status
    }
    
    # Publication des statistiques
    client.publish(monitoring_topic, json.dumps(monitoring_data), qos=1, retain=True)
    error_stats['last_monitoring_publish'] = now
    
    logger.info(f"Statistiques de monitoring publiées: {success_rate}% succès, {error_stats['consecutive_errors']} erreurs consécutives, statut: {monitoring_data['health_status']}")

def main():

    global mqtt_host
    global mqtt_port
    global lwt_topic
    global serial_port

    logger.info(" ==== Starting pzem2mqtt 1.0 (mamath) === ")

    # MQTT configuration
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.will_set(lwt_topic, "offline", qos=0, retain=True)
    client.on_connect = on_connect

    logger.info("Connection to mqtt broker : http://{}:{}".format(mqtt_host, mqtt_port))

    # client.on_log = on_log
    # client.username_pw_set(mqtt_user, mqtt_pwd)
    client.connect(mqtt_host, mqtt_port, keepalive=120)
    client.publish(lwt_topic, "online", qos=0, retain=True)

    time.sleep(4)

    # Configuration automatique de la découverte pour tous les capteurs activés
    setup_discovery_configs(client)
    
    # Configuration de la découverte pour le monitoring
    # setup_monitoring_discovery(client)

    time.sleep(2)

    # Connect to the slave avec paramètres optimisés pour la stabilité
    serial_connection = serial.Serial(
                        port=serial_port,
                        baudrate=9600,
                        bytesize=8,
                        parity='N',
                        stopbits=1,
                        xonxoff=0,
                        timeout=3.0,  # Timeout plus long pour éviter les erreurs
                        write_timeout=2.0
                        )

    master = modbus_rtu.RtuMaster(serial_connection)
    master.set_timeout(3.0)  # Timeout Modbus plus long
    master.set_verbose(True)

    try:
        master.close()
    except:
        pass

    # Planification avec l'intervalle de polling configuré
    schedule.every(poll_interval).seconds.do(process, client=client, rtu=master)

    client.loop_start()

    # Publication initiale des statistiques de monitoring
    publish_monitoring_stats(client)

    process(client, master)

    while True:
        schedule.run_pending()
        time.sleep(10)

if __name__ == "__main__":

    main()
