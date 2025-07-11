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

from datetime import datetime
from pytz import timezone


# =================== Configuration ===============================
mqtt_host = "192.168.100.9"
mqtt_port = 1883
auto_discovery = True
discovery_topic = "homeassistant"
#serial_port = "/dev/ttyUSB1"
serial_port = "/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0"
base_topic = "pzem2mqtt/003"
local_tz = "Europe/Paris"
lwt_topic = base_topic + "/lwt"
# ==================================================================

logging.basicConfig(level=logging.DEBUG, format='   %(asctime)s %(levelname)-8s %(message)s')
logger = logging.getLogger()


def on_connect(client, userdata, flags, reason_code, properties=None):
    """ Connection MQTT handler"""

    global lwt_topic
    logger.info("Connected to MQTT server with result code " + str(reason_code))

    client.publish(lwt_topic, "online", qos=1, retain=True)

#        createPowerDevice(client, "0xff02398f98e9a322", "Plaque induction energy")
#        createPowerDevice(client, "0xff021256faec456d", "Four energy")
#        createPowerDevice(client, "0xffc5654ea54c8978", "Chauffage etage energy")

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
    global base_topic
    global payload_chauffage
    global payload_chauffe_eau

    payload = getPzem004t(rtu, 1)
    if payload:
        # component_label = "Plaque induction energy"
        component_id = "plaque_induction_energy"
        client.publish(base_topic + "/" + component_id, json.dumps(payload), qos=0, retain=True)
    time.sleep(1)

    payload = getPzem004t(rtu, 2)
    time.sleep(1)

    payload = getPzem004t(rtu, 3)
    if payload:
        # component_label = "Four energy"
        component_id = "four_energy"
        client.publish(base_topic + "/" + component_id, json.dumps(payload), qos=0, retain=True)
    time.sleep(0.5)

#    payload = getPzem004t(rtu, 3)
#    if payload:
#        # component_label = "Chauffage etage energy"
#        component_id = "chauffage_etage_energy"
#        client.publish(base_topic + "/" + component_id, json.dumps(payload), qos=0, retain=True)
#    time.sleep(0.5)

def sendDiscoveryConfig(client, object_id, name):
    unique_id = f"{object_id}_{base_topic.split('/')[-1]}"
    topic_state = f"{base_topic}/{object_id}"
    topic_config = f"{discovery_topic}/sensor/{unique_id}/config"

    payload = {
        "name": name,
        "state_topic": topic_state,
        "value_template": "{{ value_json.energy }}",
        "unit_of_measurement": "kWh",
        "device_class": "energy",
        "unique_id": unique_id,
        "json_attributes_topic": topic_state,
        "device": {
            "identifiers": [base_topic],
            "name": f"PZEM004T {base_topic.split('/')[-1]}",
            "manufacturer": "Mamath",
            "model": "PZEM-004T v3.0"
        }
    }

    client.publish(topic_config, json.dumps(payload), qos=0, retain=True)

def main():

    global mqtt_host
    global mqtt_port
    global mqtt_user
    global mqtt_pwd
    global lwt_topic
    global serial

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

    sendDiscoveryConfig(client, "plaque_induction_energy", "Plaque Induction")
    sendDiscoveryConfig(client, "four_energy", "Four")
    # sendDiscoveryConfig(client, "chauffage_etage_energy", "Chauffage Étage")    

    sendDiscoveryConfig(client, "pve0_srv_energy", "PVE0 Energy")
    sendDiscoveryConfig(client, "pve1_srv_energy", "PVE1 Energy")
    sendDiscoveryConfig(client, "pve2_srv_energy", "PVE2 Energy")
    sendDiscoveryConfig(client, "pve3_srv_energy", "PVE3 Energy")


    time.sleep(2)

    # Connect to the slave
    serial = serial.Serial(
                        port=serial_port,
                        baudrate=9600,
                        bytesize=8,
                        parity='N',
                        stopbits=1,
                        xonxoff=0
                        )

    master = modbus_rtu.RtuMaster(serial)
    master.set_timeout(2.0)
    master.set_verbose(True)

    try:
        master.close()
    except:
        pass

    # schedule.every().day.at("00:00").do(process, client=client)
    # schedule.every().day.do(sendDiscoveryConfig, client=client)
    # schedule.every().minutes.do(process, client=client)
    schedule.every(5).seconds.do(process, client=client, rtu=master)

    client.loop_start()

    process(client, master)

    while True:
        schedule.run_pending()
        time.sleep(10)

if __name__ == "__main__":

    main()
