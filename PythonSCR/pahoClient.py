# python 3.9

import random
import time
import ssl

from paho.mqtt import client as mqtt_client

broker = 'localhost'
port = 1883
topic = "hello"
client_id= f'mqtt-subscription-{random.randint(0,1000)}'
username = 'mqtt-test'
password = 'mqtt-test'
connected=False
Messagerecieved=False


def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)
    # Set Connecting Client ID
    client = mqtt_client.Client(client_id)
    client.on_message= on_message
    client.username_pw_set(username, password)
    client.on_connect = on_connect    
    client.connect(broker, port)
    return client


       
def subscribe(client: mqtt_client):
    client.subscribe(topic)
    while connected!=True:
        time.sleep(0.2)
    while Messagerecieved!=True:
        time.sleep(0.2)
    client.loop_stop()
    
def on_message(client,userdata,message):
    Messagerecieved=True
    print("Message received ", str(message.payload.decode("utf-8")))
    print("Message topic = ", message.topic)
    
def run():
    client = connect_mqtt()
    client.loop_start()
    subscribe(client)
    
if __name__ == '__main__':
    run()