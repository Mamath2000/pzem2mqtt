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
# ==================================================================


def on_connect(client, userdata, flags, reason_code, properties=None):
    """ Connection MQTT handler"""

    global lwt_topic
    logger.info("Connected to MQTT server with result code " + str(reason_code))

    client.publish(lwt_topic, "online", qos=1, retain=True)

def getPzem004t(rtu, id):

    try:
        data = rtu.execute(id, cst.READ_INPUT_REGISTERS,  0, 10)

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


        logger.info("Reading PZEM004T ok. Sensor n° {0}".format(id))
        jsondata={
                    "current": float(courant),
                    "energy": float(energy),
                    "power": round(float(puissance),1),
                    "voltage": float(tension),
                    "facteur_de_puiss": float(facteurDePuiss)
                }
        return jsondata

    except:
        logger.error("Error reading PZEM004T. Sensor n° {0}".format(id))

        pass

def process(client, rtu):
    """Traite tous les capteurs configurés"""
    global base_topic, config
    
    for sensor in config['sensors']:
        if not sensor.get('enabled', True):
            logger.debug(f"Capteur {sensor['name']} désactivé, passage au suivant")
            continue
            
        logger.debug(f"Lecture du capteur {sensor['name']} (ID: {sensor['device_id']})")
        payload = getPzem004t(rtu, sensor['device_id'])
        
        if payload:
            component_id = sensor['unique_id']
            topic = f"{base_topic}/{component_id}"
            client.publish(topic, json.dumps(payload), qos=0, retain=True)
            logger.info(f"Données publiées pour {sensor['name']} sur {topic}")
        else:
            logger.warning(f"Échec de lecture du capteur {sensor['name']} (ID: {sensor['device_id']})")
            
        time.sleep(2)  # Délai entre chaque lecture de capteur

def sendDiscoveryConfig(client, sensor):
    """Envoie la configuration de découverte pour un capteur"""
    unique_id = f"{sensor['unique_id']}_energy"
    topic_state = f"{base_topic}/{sensor['unique_id']}"
    topic_config = f"{discovery_topic}/sensor/{unique_id}/config"

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
        }
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

    time.sleep(2)

    # Connect to the slave
    serial_connection = serial.Serial(
                        port=serial_port,
                        baudrate=9600,
                        bytesize=8,
                        parity='N',
                        stopbits=1,
                        xonxoff=0
                        )

    master = modbus_rtu.RtuMaster(serial_connection)
    master.set_timeout(2.0)
    master.set_verbose(True)

    try:
        master.close()
    except:
        pass

    # Planification avec l'intervalle de polling configuré
    schedule.every(poll_interval).seconds.do(process, client=client, rtu=master)

    client.loop_start()

    process(client, master)

    while True:
        schedule.run_pending()
        time.sleep(10)

if __name__ == "__main__":

    main()
