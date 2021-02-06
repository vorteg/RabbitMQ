#!/usr/bin/env python
import pika, sys, os

def main():
    login = pika.PlainCredentials('test', 'hola')
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', credentials=login))
    channel = connection.channel()

    channel.queue_declare(queue='hello2')

    def callback(ch, method, properties, body):
        print(" [x] Received %r" % body)

    channel.basic_consume(queue='hello', on_message_callback=callback, auto_ack=True)
   
    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)