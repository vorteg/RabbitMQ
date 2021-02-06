import paho.mqtt.client as mqtt
import pyodbc
import ssl
import time
import socket
from string import Template
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import json
import datetime
import shelve
import logging
import os
import sys
import getpass
import signal

# requirements: paho, pycryptodome, sendgrid, shelve
RMQ_HOST=os.getenv("RMQ_HOST")
RMQ_USERNAME=os.getenv("RMQ_USERNAME")
RMQ_PASSWORD=os.getenv("RMQ_PASSWORD")
SQL_SERVER=os.getenv("SQL_SERVER")
SQL_DATABASE=os.getenv("SQL_DATABASE")
SQL_USERNAME=os.getenv("SQL_USERNAME")
SQL_PASSWORD=os.getenv("SQL_PASSWORD")

subscriptionPattern = "#" # All topics

# if len(sys.argv) < 2 or sys.argv[1] == "loki":
#     import logging_loki
#     LOKI_HOST=os.environ["LOKI_HOST"]
#     LOKI_USERNAME=os.environ["LOKI_USERNAME"]
#     LOKI_PASSWORD=os.environ["LOKI_PASSWORD"]

#     handler = logging_loki.LokiHandler(
#         url = LOKI_HOST + "/loki/api/v1/push",
#         tags = {"service": "bridge-logger", "instance": socket.gethostname() },
#         auth = ( LOKI_USERNAME, LOKI_PASSWORD ),
#         version="1",
#     )
# elif sys.argv[1] == "stdout":
#     handler = logging.StreamHandler(sys.stdout)
# else:
#    raise SyntaxError("Unsupported logging sink '%s'." %sys.argv[1])
    

# logger = logging.getLogger("bridge-logger")
# logger.addHandler(handler)

# logging.getLogger().setLevel(logging.INFO)


def LoadCryptoKeysFromDatabase():
    cryptoKeys = {} # dict with bridge ANTSN key, dicts with 'key', 'serial' and 'type' keys as value
    sqlConnectionString = Template('Driver={ODBC Driver 17 for SQL Server};'
                      'Server=${server};'
                      'Database=${database};'
                      'UID=${username};PWD=${password};'
                      'Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;').substitute(server=SQL_SERVER, database=SQL_DATABASE, username=SQL_USERNAME, password=SQL_PASSWORD)
    conn = pyodbc.connect(sqlConnectionString)
    cursor = conn.cursor()
 
    # Check if devices table is Devices or SRDevices.
    try:   
        # Sloan or Core database 
        cursor.execute("select CONVERT(VARCHAR(MAX), DEV.ANTSerialNumber, 1) as ANTSN, "
                   "CONVERT(VARCHAR(MAX), DEV.CryptoKey3, 1) as CryptoKey, DEV.SerialNumber, TYP.Name "
                   "from DBO.Devices DEV "
                   "INNER JOIN DBO.DeviceTypes TYP on DEV.DeviceTypeId=TYP.Id "
                  )
    except:
        # Retail database
        cursor.execute("select CONVERT(VARCHAR(MAX), DEV.ANTSerialNumber, 1) as ANTSN, "
                   "CONVERT(VARCHAR(MAX), DEV.CryptoKey3, 1) as CryptoKey, DEV.SerialNumber, TYP.Name "
                   "from DBO.SRDevices DEV "
                   "INNER JOIN DBO.SRDeviceTypes TYP on DEV.SRDeviceTypeId=TYP.Id "
                  )

    for row in cursor:
        cryptoKeys[row[0]] = { 'key': row[1], 'serial': row[2], 'type': row[3] }
        
    return cryptoKeys

def OnConnect(client, userdata, flags, rc):
    print("Connection status %d." %rc)
    if (rc == 0):
        print("Subscribing to topic %s" %subscriptionPattern)
        client.subscribe(topic=subscriptionPattern, qos=0)

def OnDisconnect(client, userdata, rc):
    print("Disconnected from MQTT broker " + str(rc))
    
def OnMessage(client, userdata, message):
    topicParts = message.topic.split("/")
    if (topicParts[0].startswith("SRMQ")):
        bridge = topicParts[1]
        iv = topicParts[3]
    else:
        bridge = topicParts[0]
        iv = topicParts[2]

    now = datetime.datetime.now()
    if (bridge in userdata):
        try:
            cipher = AES.new(bytes.fromhex(userdata[bridge]['key'][2:]), AES.MODE_CBC, bytes.fromhex(iv[2:]))
            msg = cipher.decrypt(message.payload)
            msg = msg.split(b'\0',1)[0] # remove null chars \x00

            d = json.loads(msg.decode('ascii')) # Drop the null terminator '\x00' at the end.
            logger.info(message.topic + ":" + msg.decode('ascii'), extra={"tags":{"bridge": bridge }})

            # {'Header': {'Ver': 1, 'Time': 1598454922}, 'AntSN': '0xBB7796C9', 'DeviceTime': 1598454905, 'Status': 5, 'BatteryLevel': 60, 'rssiDnLink': -65}
            print(bridge + ":" + message.topic)
        except Exception as e:
            print(e)
        
cryptoKeys = LoadCryptoKeysFromDatabase()
print("Loaded %d devices and their keys from database %s." %(len(cryptoKeys.keys()), SQL_DATABASE))
client = mqtt.Client("BridgeMonitor_%s@%s" %(getpass.getuser(), socket.gethostname()), userdata=cryptoKeys)
client.username_pw_set(username=RMQ_USERNAME, password=RMQ_PASSWORD)
client.tls_set(cert_reqs=ssl.CERT_NONE)
client.tls_insecure_set(True)
print("Connecting to %s" %RMQ_HOST)
client.on_message = OnMessage
client.on_connect = OnConnect
client.on_disconnect = OnDisconnect

signal.signal(signal.SIGINT, lambda num, frame:sys.exit(0))
client.connect(RMQ_HOST, 8883, 60)

while True:
    client.loop(2)
    time.sleep(.1)


