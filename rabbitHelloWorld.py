import pika 
import json
con = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = con.channel()
channel.queue_declare(queue='hello')
payload = {'quote': 'abc'}
channel.basic_publish(exchange='',routing_key='hello',body=json.dumps(payload))
print (" [X] SENT 'hello world'")
con.close()

