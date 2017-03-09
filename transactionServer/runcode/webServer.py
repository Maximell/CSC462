import time
import json
import pika
from flask import Flask, request
from rabbitMQSetups import RabbitMQClient, RabbitMQReceiver

app = Flask(__name__)


# args now has keys: userId , sym , lineNum , command , cash

def sendtoQueue(data):
    transactionClient.send(data, priority=1)


@app.route('/add/<string:userId>/', methods=['POST'])
def add(userId):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    cash = float(request.form['cash'].decode('utf-8'))
    data = {"command": "ADD", "userId": userId, "cash": cash, "lineNum": lineNum}
    # initializing the stuff for the return
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    args = {'x-max-priority': 2}
    channel.queue_declare(queue=RabbitMQReceiver.WEB+str(lineNum), arguments=args)
    # send data to transactionServer
    sendtoQueue(data)
    print("waiting for transaction return")
    result = (None, None, None)
    while result is not (None, None, None):
        time.sleep(0.1)
        result = channel.basic_get(queue=RabbitMQReceiver.WEB+str(lineNum))
        print "interm result was: ", result
    print "from the trans server: ", result
    return result
    #return RabbitMQReceiver(None, RabbitMQReceiver.WEB + str(lineNum))
    #return 'Trying to add %f cash to user %s.' % (cash, userId)


@app.route('/quote/<string:userId>/<string:stockSymbol>/', methods=['GET'])
def quote(userId, stockSymbol):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    data = {"lineNum": lineNum, "command": "QUOTE", "userId": userId, "stockSymbol": stockSymbol}
    sendtoQueue(data)
    return 'Getting a quote for user %s on stock %s.' % (userId, stockSymbol)


@app.route('/buy/<string:userId>/<string:stockSymbol>/', methods=['POST'])
def buy(userId, stockSymbol):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    cash = float(request.form['cash'].decode('utf-8'))
    data = {"command": "BUY", "userId": userId, "stockSymbol": stockSymbol, "cash": cash, "lineNum": lineNum}
    sendtoQueue(data)
    return 'Buying stock %s for user %s for cash %f' % (stockSymbol, userId, cash)


@app.route('/commit-buy/<string:userId>/', methods=['POST'])
def commitBuy(userId):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    data = {"command": "COMMIT_BUY", "userId": userId, "lineNum": lineNum}
    sendtoQueue(data)
    return 'Committing buy for user %s.' % (userId)


@app.route('/cancel-buy/<string:userId>/', methods=['POST'])
def cancelBuy(userId):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    data = {"command": "CANCEL_BUY", "userId": userId, "lineNum": lineNum}
    sendtoQueue(data)
    return 'Cancelling buy for user %s.' % (userId)


@app.route('/sell/<string:userId>/<string:stockSymbol>/', methods=['POST'])
def sell(userId, stockSymbol):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    cash = float(request.form['cash'].decode('utf-8'))
    data = {"command": "SELL", "userId": userId, "stockSymbol": stockSymbol, "cash": cash, "lineNum": lineNum}
    sendtoQueue(data)
    return 'Selling %f of stock %s for user %s' % (cash, stockSymbol, userId)


@app.route('/commit-sell/<string:userId>/', methods=['POST'])
def commitSell(userId):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    data = {"command": "COMMIT_SELL", "userId": userId, "lineNum": lineNum}
    sendtoQueue(data)
    return 'Committing sell for user %s.' % (userId)


@app.route('/cancel-sell/<string:userId>/', methods=['POST'])
def cancelSell(userId):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    data = {"command": "CANCEL_SELL", "userId": userId, "lineNum": lineNum}
    sendtoQueue(data)
    return 'Cancelling sell for user %s.' % (userId)


@app.route('/set-buy-amount/<string:userId>/<string:stockSymbol>/', methods=['POST'])
def setBuyAmount(userId, stockSymbol):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    cash = float(request.form['cash'].decode('utf-8'))
    data = {"command": "SET_BUY_AMOUNT", "userId": userId, "stockSymbol": stockSymbol, "cash": cash, "lineNum": lineNum}
    sendtoQueue(data)
    return 'Setting buy of $%f on stock %s for user %s.' % (cash, stockSymbol, userId)


@app.route('/cancel-set-buy/<string:userId>/<string:stockSymbol>/', methods=['POST'])
def cancelSetBuy(userId, stockSymbol):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    data = {"command": "CANCEL_SET_BUY", "userId": userId, "stockSymbol": stockSymbol, "lineNum": lineNum}
    sendtoQueue(data)
    return 'Cancelling set buy for user %s on stock %s.' % (userId, stockSymbol)


@app.route('/set-buy-trigger/<string:userId>/<string:stockSymbol>/', methods=['POST'])
def setBuyTrigger(userId, stockSymbol):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    cash = float(request.form['cash'].decode('utf-8'))
    data = {"command": "SET_BUY_TRIGGER", "userId": userId, "stockSymbol": stockSymbol, "cash": cash, "lineNum": lineNum}
    sendtoQueue(data)
    return 'Setting a buy trigger for user %s on stock %s for cash %f.' % (userId, stockSymbol, cash)


@app.route('/set-sell-amount/<string:userId>/<string:stockSymbol>/', methods=['POST'])
def setSellAmount(userId, stockSymbol):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    cash = float(request.form['cash'].decode('utf-8'))
    data = {"command": "SET_SELL_AMOUNT", "userId": userId, "stockSymbol": stockSymbol, "cash": cash, "lineNum": lineNum}
    sendtoQueue(data)
    return 'Setting a sell for user %s on stock %s for cash %f.' % (userId, stockSymbol, cash)


@app.route('/set-sell-trigger/<string:userId>/<string:stockSymbol>/', methods=['POST'])
def setSellTrigger(userId, stockSymbol):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    cash = float(request.form['cash'].decode('utf-8'))
    data = {"command": "SET_SELL_TRIGGER", "userId": userId, "stockSymbol": stockSymbol, "cash": cash, "lineNum": lineNum}
    sendtoQueue(data)
    return 'Setting a sell trigger for user %s on stock %s for cash %f.' % (userId, stockSymbol, cash)


@app.route('/cancel-set-sell/<string:userId>/<string:stockSymbol>/', methods=['POST'])
def cancelSetSell(userId, stockSymbol):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    data = {"command": "CANCEL_SET_SELL", "userId": userId, "stockSymbol": stockSymbol, "lineNum": lineNum}
    sendtoQueue(data)
    return 'Cancelling set sell for user %s on stock %s.' % (userId, stockSymbol)


@app.route('/dumplog/', methods=['POST'])
def dumpLog():
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    fileName = request.form['fileName']
    # print "dumplog"
    data = {"command": "DUMPLOG", "lineNum": lineNum, "userId": fileName}
    sendtoQueue(data)
    return 'Dumping log into file: %s.' % (fileName)


@app.route('/display-summary/<string:userId>/', methods=['GET'])
def displaySummary(userId):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    data = {"command": "DISPLAY_SUMMARY", "userId": userId, "lineNum": lineNum}
    sendtoQueue(data)
    return 'Displaying summary for user %s.' % (userId)


if __name__ == '__main__':
    transactionClient = RabbitMQClient(RabbitMQClient.TRANSACTION)
    app.run()
