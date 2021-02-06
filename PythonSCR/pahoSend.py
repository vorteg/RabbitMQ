# python 3.9

import random
import time
import json
from paho.mqtt import client as mqtt_client

broker = 'localhost'
port = 1883
topic = "hello"
client_id= f'mqtt-subscription-{random.randint(0,1000)}'
username = 'mqtt-test'
password = 'mqtt-test'


def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)
    # Set Connecting Client ID
    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect    
    client.connect(broker, port)
    return client


def jsonReadFiles():
    with open('testData.json') as json_file:
        data = json.load(json_file)
    return data

def publish(client):
     msg_count = 0
     while True:
         time.sleep(1)
        # msg = f"messages: holi!! {msg_count}"
         msg = jsonReadFiles()
         msg = json.dumps(msg)
         result = client.publish(topic, msg)
         # result: [0, 1]
         status = result[0]
         if status == 0:
             print(f"Send `{msg}` to topic `{topic}`")
         else:
             print(f"Failed to send message to topic {topic}")
         msg_count += 1     
   
  
def run():
    client = connect_mqtt()
    client.loop_start()
    publish(client)
    
    
if __name__ == '__main__':
    run()