import time
import json
import pika
from flask import Flask, request
from rabbitMQSetups import RabbitMQClient, RabbitMQReceiver
import socket


app = Flask(__name__)


# args now has keys: userId , sym , lineNum , command , cash

def sendToQueue(data):
    transactionClient.send(data, priority=1)


def sendAndReceive(data, host='localhost', queueName=None):
    # if the queueName is None, set it to a default

    if queueName is None:
        try:
            queueName = RabbitMQReceiver.WEB + str(data["lineNum"])
        except KeyError as error:
            print error
    # send a request to the transactionServer
    sendToQueue(data)
    # open a connection to rabbitMq
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
    channel = connection.channel()
    # declare a queue
    args = {'x-max-priority': 2}
    channel.queue_declare(queue=queueName, arguments=args)
    print("waiting for transaction return on queue: ", queueName)
    # wait for a response from the transactionServer in that queue
    result = None
    while result is None:
        time.sleep(0.01)
        method, props, result = channel.basic_get(queue=queueName)
    print "from the trans server: ", result
    # close the channel
    channel.close()
    return result


@app.route('/add/<string:userId>/', methods=['POST'])
def add(userId):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    try:
        cash = float(request.form['cash'].decode('utf-8'))
    except:
        data = {"command": "ADD", "userId": userId, "cash": -1, "lineNum": None}
        sendtoQueue(data)
        return "Can't convert Value to float" , request.form['cash'].decode('utf-8')
    data = {"command": "ADD", "userId": userId, "cash": cash, "lineNum": lineNum}

    return sendAndReceive(data)


@app.route('/quote/<string:userId>/<string:stockSymbol>/', methods=['GET'])
def quote(userId, stockSymbol):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    data = {"lineNum": lineNum, "command": "QUOTE", "userId": userId, "stockSymbol": stockSymbol}

    return sendAndReceive(data)


@app.route('/buy/<string:userId>/<string:stockSymbol>/', methods=['POST'])
def buy(userId, stockSymbol):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    try:
        cash = float(request.form['cash'].decode('utf-8'))
    except:
        data = {"command": "ADD", "userId": userId, "cash": -1, "lineNum": None}
        sendtoQueue(data)
        return "Can't convert Value to float" , request.form['cash'].decode('utf-8')
    data = {"command": "BUY", "userId": userId, "stockSymbol": stockSymbol, "cash": cash, "lineNum": lineNum}

    return sendAndReceive(data)


@app.route('/commit-buy/<string:userId>/', methods=['POST'])
def commitBuy(userId):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    data = {"command": "COMMIT_BUY", "userId": userId, "lineNum": lineNum}

    return sendAndReceive(data)


@app.route('/cancel-buy/<string:userId>/', methods=['POST'])
def cancelBuy(userId):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    data = {"command": "CANCEL_BUY", "userId": userId, "lineNum": lineNum}

    return sendAndReceive(data)


@app.route('/sell/<string:userId>/<string:stockSymbol>/', methods=['POST'])
def sell(userId, stockSymbol):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    try:
        cash = float(request.form['cash'].decode('utf-8'))
    except:
        data = {"command": "ADD", "userId": userId, "cash": -1, "lineNum": None}
        sendtoQueue(data)
        return "Can't convert Value to float" , request.form['cash'].decode('utf-8')
    data = {"command": "SELL", "userId": userId, "stockSymbol": stockSymbol, "cash": cash, "lineNum": lineNum}

    return sendAndReceive(data)


@app.route('/commit-sell/<string:userId>/', methods=['POST'])
def commitSell(userId):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    data = {"command": "COMMIT_SELL", "userId": userId, "lineNum": lineNum}

    return sendAndReceive(data)


@app.route('/cancel-sell/<string:userId>/', methods=['POST'])
def cancelSell(userId):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    data = {"command": "CANCEL_SELL", "userId": userId, "lineNum": lineNum}

    return sendAndReceive(data)


@app.route('/set-buy-amount/<string:userId>/<string:stockSymbol>/', methods=['POST'])
def setBuyAmount(userId, stockSymbol):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    try:
        cash = float(request.form['cash'].decode('utf-8'))
    except:
        data = {"command": "ADD", "userId": userId, "cash": -1, "lineNum": None}
        sendtoQueue(data)
        return "Can't convert Value to float" , request.form['cash'].decode('utf-8')
    data = {"command": "SET_BUY_AMOUNT", "userId": userId, "stockSymbol": stockSymbol, "cash": cash, "lineNum": lineNum}

    return sendAndReceive(data)


@app.route('/cancel-set-buy/<string:userId>/<string:stockSymbol>/', methods=['POST'])
def cancelSetBuy(userId, stockSymbol):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    data = {"command": "CANCEL_SET_BUY", "userId": userId, "stockSymbol": stockSymbol, "lineNum": lineNum}

    return sendAndReceive(data)


@app.route('/set-buy-trigger/<string:userId>/<string:stockSymbol>/', methods=['POST'])
def setBuyTrigger(userId, stockSymbol):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    try:
        cash = float(request.form['cash'].decode('utf-8'))
    except:
        data = {"command": "ADD", "userId": userId, "cash": -1, "lineNum": None}
        sendtoQueue(data)
        return "Can't convert Value to float" , request.form['cash'].decode('utf-8')
    data = {"command": "SET_BUY_TRIGGER", "userId": userId, "stockSymbol": stockSymbol, "cash": cash, "lineNum": lineNum}

    return sendAndReceive(data)


@app.route('/set-sell-amount/<string:userId>/<string:stockSymbol>/', methods=['POST'])
def setSellAmount(userId, stockSymbol):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    try:
        cash = float(request.form['cash'].decode('utf-8'))
    except:
        data = {"command": "ADD", "userId": userId, "cash": -1, "lineNum": None}
        sendtoQueue(data)
        return "Can't convert Value to float" , request.form['cash'].decode('utf-8')
    data = {"command": "SET_SELL_AMOUNT", "userId": userId, "stockSymbol": stockSymbol, "cash": cash, "lineNum": lineNum}

    return sendAndReceive(data)


@app.route('/set-sell-trigger/<string:userId>/<string:stockSymbol>/', methods=['POST'])
def setSellTrigger(userId, stockSymbol):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    try:
        cash = float(request.form['cash'].decode('utf-8'))
    except:
        data = {"command": "ADD", "userId": userId, "cash": -1, "lineNum": None}
        sendtoQueue(data)
        return "Can't convert Value to float" , request.form['cash'].decode('utf-8')
    data = {"command": "SET_SELL_TRIGGER", "userId": userId, "stockSymbol": stockSymbol, "cash": cash, "lineNum": lineNum}

    return sendAndReceive(data)


@app.route('/cancel-set-sell/<string:userId>/<string:stockSymbol>/', methods=['POST'])
def cancelSetSell(userId, stockSymbol):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    data = {"command": "CANCEL_SET_SELL", "userId": userId, "stockSymbol": stockSymbol, "lineNum": lineNum}

    return sendAndReceive(data)


@app.route('/dumplog/', methods=['POST'])
def dumpLog():
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    fileName = request.form['fileName']
    # print "dumplog"
    data = {"command": "DUMPLOG", "lineNum": lineNum, "userId": fileName}

    return sendAndReceive(data)


@app.route('/display-summary/<string:userId>/', methods=['GET'])
def displaySummary(userId):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    data = {"command": "DISPLAY_SUMMARY", "userId": userId, "lineNum": lineNum}

    return sendAndReceive(data)


if __name__ == '__main__':
    transactionClient = RabbitMQClient(RabbitMQClient.TRANSACTION)
    app.run(host="0.0.0.0",port=44424) 
