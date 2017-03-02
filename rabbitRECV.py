import pika 
import json
con = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = con.channel()
channel.queue_declare(queue='hello')

def callback(ch , method , properties, body):
    print(" [x] Recieved %r" % json.loads(body))

channel.basic_consume(callback, queue='hello', no_ack=True)

print("[x] waiting for message,, pres CTRL+C to exit")
channel.start_consuming()
    

