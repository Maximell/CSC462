import sys
import time
from pprint import pprint
import json
import pika

# tried to import -> code completion worked, running it didnt, why is python like this
# from transactionServer.runCode.rabbitMQSetups import RabbitMQClient
class RabbitMQClient():
    def __init__(self, queueName):
        self.queueName = queueName
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('142.104.91.142', 44429))
        self.channel = self.connection.channel()

        args = {'x-max-priority': 2}
        self.channel.queue_declare(queue=self.queueName, arguments=args)

    def send(self, requestBody):
        properties = pika.BasicProperties(priority=1)
        self.channel.basic_publish(
            exchange='',
            routing_key=self.queueName,
            properties=properties,
            body=json.dumps(requestBody),

        )


# Worker machines via queues + mac
workerMap = [
    [RabbitMQClient("transactionIn193596476298033"), 0],
    [RabbitMQClient("transactionIn193596744799041"), 0],
    [RabbitMQClient("transactionIn193601473895188"), 0],
    [RabbitMQClient("transactionIn193601742334740"), 0],
    [RabbitMQClient("transactionIn193809078333764"), 0],
    [RabbitMQClient("transactionIn193821963432263"), 0],
    [RabbitMQClient("transactionIn193826241687624"), 0],
    [RabbitMQClient("transactionIn193830553497929"), 0],
    [RabbitMQClient("transactionIn193860618727760"), 0],
    [RabbitMQClient("transactionIn8796760983851"), 0]
]
# transactionClient.send(data, priority=1)

# User to Worker Mapping.
userMap = {}


def send(command, args, lineNum):
    print "--------------------"
    print "command", command
    print "args", args
    print "line", lineNum
    user = args[0]

    # get or put into userMap
    if user in userMap:
        client = userMap[user]
        # print("In dict already")
    else:
        min = workerMap[0][1]
        index = 0
        for x in range(0, len(workerMap)):
            currentWorker = workerMap[x]
            if currentWorker[1] <= min:
                sendto = currentWorker
                index = x
                min = currentWorker[1]
        if sendto != None:
            # print("adding User to map")
            userMap[user] = sendto[0]
            client = sendto[0]
            workerMap[index][1] += 1
        else:
            print("problem setting user map")

    # setup args to push into rabbit
    if len(args) > 2:
        args = {
            'userId': args[0],
            'stockSymbol': args[1],
            'cash': args[2]
        }
    elif len(args) == 2 and command in ['ADD']:
        args = {
            'userId': args[0],
            'cash': args[1]
        }
    elif len(args) == 2:
        args = {
            'userId': args[0],
            'stockSymbol': args[1]
        }
    elif len(args) == 1 and command in ['DUMPLOG']:
        # TODO: remove the sleep, temp solution
        time.sleep(10)
        args = {
            'userId': args[0]
        }
    elif len(args) == 1:
        args = {
            'userId': args[0]
        }

    args["command"] = command
    args["lineNum"] = lineNum

    if args.get("cash"):
        try:
            float(args["cash"])
        except:
            args["cash"] = -1

    print "sending:", args
    # push into rabbit
    client.send(args)


def main():
    # read file and push into queues as you are reading
    with open(sys.argv[1]) as f:
        for line in f:
            line = line.strip()
            splitLine = line.split(" ")

            lineNumber = splitLine[0].strip("[]")

            commandAndArgs = splitLine[1].split(",")
            command = commandAndArgs[0]
            args = commandAndArgs[1:]

            send(command, args, lineNumber)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('INCORRECT PARAMETERS\n')
        print('python rabbitTestDriver.py  <file>')
        print('example: python rabbitTestDriver.py 2userWorkLoad.txt')
        print(sys.argv)
    else:
        main()

        pprint(workerMap)

        print('completed')

