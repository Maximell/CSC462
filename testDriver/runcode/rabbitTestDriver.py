import sys
import time
from pprint import pprint
import json
import pika

# tried to import -> code completion worked, running it didnt, why is python like this
# from transactionServer.runCode.rabbitMQSetups import RabbitMQClient
# class RabbitMQClient():
#     def __init__(self, queueName):
#         self.queueName = queueName
#         self.connection = pika.BlockingConnection(pika.ConnectionParameters('142.104.91.142', 44429))
#         self.channel = self.connection.channel()
#
#         args = {'x-max-priority': 3 , 'x-message-ttl': 600000 }
#         self.channel.queue_declare(queue=self.queueName, arguments=args)
#
#     def send(self, requestBody , properties):
#         self.channel.basic_publish(
#             exchange='',
#             routing_key=self.queueName,
#             properties=properties,
#             body=json.dumps(requestBody),
#
#         )
class RabbitMQClient():
    def __init__(self, queueName):
        self.queueName = queueName
        self.param = pika.ConnectionParameters('142.104.91.142',44429)
        # self.channel = self.connection.channel(self.send)
        #
        # self.channel.queue_declare(self.send,queue=self.queueName, arguments=args)

        self.connection = pika.SelectConnection(parameters=self.param,on_open_callback=self.send)
        try:
            self.connection.ioloop.start()
        except:
            self.connection.close()
            self.connection.ioloop.start()

    def on_open(self):
        self.channel = self.connection.channel(self.send)
    def send(self, requestBody , properties):
        self.channel.basic_publish(
            exchange='',
            routing_key=self.queueName,
            properties=properties,
            body=json.dumps(requestBody),

        )
        self.connection.close()


# Worker machines via queues + mac
workerMap = [
    #  QueueName , [NumOfUsers , Number of Commands]
    [RabbitMQClient("transactionIn193596476298033"), [0 , 0]], #B01331331331
    [RabbitMQClient("transactionIn193596744799041"), [0 , 0]], #B01341341341
    [RabbitMQClient("transactionIn193601473895188"), [0 , 0]], #B0145B145B14
    [RabbitMQClient("transactionIn193601742334740"), [0 , 0]], #B0146B146B14
    [RabbitMQClient("transactionIn193809078333764"), [0 , 0]], #B044B144B144
    [RabbitMQClient("transactionIn193821963432263"), [0 , 0]], #B047B147B147
    [RabbitMQClient("transactionIn193826241687624"), [0 , 0]], # B048B048B048
    [RabbitMQClient("transactionIn193830553497929"), [0 , 0]], #B049B149B149
    [RabbitMQClient("transactionIn193860618727760"), [0 , 0]], #B050B150B150
    [RabbitMQClient("transactionIn8796760983851"), [0 , 0]] #B132
]
# last mac addr queue is 132 - Haven't changed the mac yet.

# transactionClient.send(data, priority=1)

# User to Worker Mapping.
userMap = {}


def send(command, args, lineNum):
    print "--------------------"
    print "command", command
    print "args", args
    print "line", lineNum
    user = args[0]
    properties = pika.BasicProperties(priority=1)

    # get or put into userMap
    if user in userMap:
        client = userMap[user]
        for x in workerMap:
            # update the ammount in the current Worker
            if x[0] == client:
                x[1][1] += 1
                break

        # print("In dict already")
    else:
        # just need a number in the workerMap
        minUser = workerMap[0][1][0]
        index = 0
        sendto = None
        # find the worker with the fewest users
        for x in range(0, len(workerMap)):
            currentWorker = workerMap[x]
            currentAmount = currentWorker[1][1]

            if currentWorker[1][0] <= minUser:
                sendto = currentWorker
                index = x
                print "found fewest users"
                minUser = currentWorker[1][0]
                minAmount = currentAmount
        # find the worker with fewest users and commands.
        for x in range(0 , len(workerMap)):
            currentWorker = workerMap[x]
            # if user amount is greater than minUser skip
            if currentWorker[1][0] > minUser:
                continue
            else:
                # SAme amount of user so check amount
                if currentWorker[1][1] < minAmount:
                    index = x
                    minAmount = currentWorker[1][1]
                    print "found fewest Commands"
                    sendto = currentWorker
        if sendto != None:
            # print("adding User to map")
            userMap[user] = sendto[0]
            client = sendto[0]
            workerMap[index][1][1] += 1
            workerMap[index][1][0] += 1
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
        args = {
            'userId': "./testLOG"
        }
        properties = pika.BasicProperties(priority=3)
        # return  # dont bother sending a dumplog
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
    client.send(args , properties)


def main():
    # read file and push into queues as you are reading
    users = {}
    with open(sys.argv[1]) as f:
        for line in f:
            line = line.strip()
            splitLine = line.split(" ")

            lineNumber = splitLine[0].strip("[]")

            commandAndArgs = splitLine[1].split(",")
            command = commandAndArgs[0]
            args = commandAndArgs[1:]
            # record how many commands each user gets

            #If Dumplog then send the dumplog to the user with the highest amount of commands
            if command in ['DUMPLOG']:
                max = 0
                workerQueue = workerMap[0][0]
                for worker in workerMap:
                    if worker[1][1] > max:
                        max = worker[1][1]
                        workerQueue = worker[0]
                for user in userMap:
                    if workerQueue == userMap[user]:
                        args[0] = user

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
        pprint(userMap.items())
        print('completed')

