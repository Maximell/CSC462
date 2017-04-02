import time
import json
import pika
import random
from flask import Flask, request, render_template
from rabbitMQSetups import RabbitMQClient, RabbitMQReceiver


app = Flask(__name__)

# args now has keys: userId , sym , lineNum , command , cash

def sendToQueue(data):
    transactionClient.send(data, priority=1)


def sendAndReceive(data, host='142.104.91.142',port=44429, queueName=None):
    # if the queueName is None, set it to a default
    if queueName is None:
        try:
            queueName = RabbitMQReceiver.WEB + str(data["lineNum"])
        except KeyError as error:
            print error
    # send a request to the transactionServer
    sendToQueue(data)
    # open a connection to rabbitMq
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=host, port=port))
    channel = connection.channel()
    # declare a queue
    args = {'x-max-priority': 3, 'x-message-ttl': 600000}
    channel.queue_declare(queue=queueName, arguments=args)
    print("waiting for transaction return on queue: ", queueName)
    # wait for a response from the transactionServer in that queue
    result = None
    while result is None:
        try:
            time.sleep(0.01)
            method, props, result = channel.basic_get(queue=queueName)
        except Exception as e:
            print e

    print "from the trans server: ", result
    # close the channel
    channel.close()
    return result

def getRandomRequestLineNum(start=-100000, stop=-1, step=1):
    print "in get random"
    result = random.randrange(start, stop, step)
    print "result: ", result
    return result

# Home
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# Add methods
def doAdd(userId, cash, lineNum=0):
    data = {"command": "ADD", "userId": userId, "cash": cash, "lineNum": lineNum}
    return sendAndReceive(data)

@app.route('/api/add/<string:userId>/', methods=['POST'])
def apiAdd(userId):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    try:
        cash = float(request.form['cash'].decode('utf-8'))
    except:
        return "Can't convert cash value to float" , request.form['cash'].decode('utf-8')
    return doAdd(userId, cash, lineNum)

@app.route('/add/', methods=['POST'])
def add():
    try:
        userId = request.form.getlist('userId')[0]
        cash = float(request.form.getlist("cash")[0])
    except:
        print "something went wrong parsing the data."
        return "something went wrong parsing the data."
    result = doAdd(userId, cash, getRandomRequestLineNum())
    return render_template('result.html', result=result)

# Quote methods
def doQuote(userId, stockSumbol, lineNum=0):
    data = {"command": "QUOTE", "userId": userId, "stockSymbol": stockSumbol, "lineNum": lineNum}
    print "doing a quote with data: ", data
    return sendAndReceive(data)

@app.route('/api/quote/<string:userId>/<string:stockSymbol>/', methods=['GET'])
def apiQuote(userId, stockSymbol):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    return doQuote(userId, stockSymbol, lineNum)

@app.route('/quote/', methods=['GET', 'POST'])
def quote():
    try:
        print request
        print request.form
        userId = request.form.getlist('userId')[0]
        print userId
        stockSymbol = request.form.getlist('stockSymbol')[0]
        print stockSymbol
    except:
        print "something went wrong parsing the data."
        return "something went wrong parsing the data."
    result = doQuote(userId, stockSymbol, getRandomRequestLineNum())
    return render_template('result.html', result=result)

# Buy methods
def doBuy(userId, stockSymbol, cash, lineNum=0):
    data = {"command": "BUY", "userId": userId, "stockSymbol": stockSymbol, "cash": cash, "lineNum": lineNum}
    return sendAndReceive(data)

@app.route('/api/buy/<string:userId>/<string:stockSymbol>/', methods=['POST'])
def apiBuy(userId, stockSymbol):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    try:
        cash = float(request.form['cash'].decode('utf-8'))
    except:
        return "Can't convert cash value to float" , request.form['cash'].decode('utf-8')
    return doBuy(userId, stockSymbol, cash, lineNum)

@app.route('/buy/', methods=['POST'])
def buy():
    try:
        userId = request.form.getlist('userId')[0]
        stockSymbol = request.form.getlist('stockSymbol')[0]
        cash = float(request.form.getlist('cash')[0])
    except:
        print "something went wrong getting data."
    return doBuy(userId, stockSymbol, cash)

# Commit Buy methods
def doCommitBuy(userId, lineNum=0):
    data = {"command": "COMMIT_BUY", "userId": userId, "lineNum": lineNum}
    return sendAndReceive(data)

@app.route('/api/commit-buy/<string:userId>/', methods=['POST'])
def apiCommitBuy(userId):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    return doCommitBuy(userId, lineNum)

@app.route('/commit-buy/', methods=['POST'])
def commitBuy():
    try:
        userId = request.form.getlist('userId')[0]
    except:
        print "something went wrong getting data."
        return
    result = doCommitBuy(userId)
    return render_template('result.html', result=result)

# Cancel Buy methods
def doCancelBuy(userId, lineNum=0):
    data = {"command": "CANCEL_BUY", "userId": userId, "lineNum": lineNum}
    return sendAndReceive(data)

@app.route('/api/cancel-buy/<string:userId>/', methods=['POST'])
def apiCancelBuy(userId):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    return doCancelBuy(userId, lineNum)

@app.route('/cancel-buy/', methods=['POST'])
def cancelBuy():
    try:
        userId = request.form.getlist('userId')[0]
    except:
        print "something went wrong getting data."
        return
    result = doCommitBuy(userId)
    return render_template('result.html', result=result)

# Sell methods
def doSell(userId, stockSymbol, cash, lineNum=0):
    data = {"command": "SELL", "userId": userId, "stockSymbol": stockSymbol, "cash": cash, "lineNum": lineNum}
    return sendAndReceive(data)

@app.route('/api/sell/<string:userId>/<string:stockSymbol>/', methods=['POST'])
def apiSell(userId, stockSymbol):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    try:
        cash = float(request.form['cash'].decode('utf-8'))
    except:
        return "Can't convert cash value to float" , request.form['cash'].decode('utf-8')
    return doSell(userId, stockSymbol, cash, lineNum)

@app.route('/sell/', methods=['POST'])
def sell():
    try:
        userId = request.form.getlist('userId')[0]
        stockSymbol = request.form.getlist('stockSymbol')[0]
        cash = float(request.form.getlist('cash')[0])
    except:
        print "something went wrong getting data."
        return
    result = doSell(userId, stockSymbol, cash)
    return render_template('result.html', result=result)

# Commit Sell methods
def doCommitSell(userId, lineNum=0):
    data = {"command": "COMMIT_SELL", "userId": userId, "lineNum": lineNum}
    return sendAndReceive(data)

@app.route('/api/commit-sell/<string:userId>/', methods=['POST'])
def apiCommitSell(userId):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    return doCommitSell(userId, lineNum)

@app.route('/commit-sell/', methods=['POST'])
def commitSell():
    try:
        userId = request.form.getlist('userId')[0]
    except:
        print "something went wrong getting data."
        return
    result = doCommitSell(userId)
    return render_template('result.html', result=result)

# Cancel Sell methods
def doCancelSell(userId, lineNum=0):
    data = {"command": "CANCEL_SELL", "userId": userId, "lineNum": lineNum}
    return sendAndReceive(data)

@app.route('/api/cancel-sell/<string:userId>/', methods=['POST'])
def apiCancelSell(userId):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    return doCommitSell(userId, lineNum)

@app.route('/cancel-sell/', methods=['POST'])
def cancelSell():
    try:
        userId = request.form.getlist('userId')[0]
    except:
        print "something went wrong getting data."
        return
    result = doCommitSell(userId)
    return render_template('result.html', result=result)

# Set Buy Amount methods
def doSetBuyAmount(userId, stockSymbol, cash, lineNum=0):
    data = {"command": "SET_BUY_AMOUNT", "userId": userId, "stockSymbol": stockSymbol, "cash": cash, "lineNum": lineNum}
    return sendAndReceive(data)

@app.route('/api/set-buy-amount/<string:userId>/<string:stockSymbol>/', methods=['POST'])
def apiSetBuyAmount(userId, stockSymbol):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    try:
        cash = float(request.form['cash'].decode('utf-8'))
    except:
        return "Can't convert cash value to float" , request.form['cash'].decode('utf-8')
    return doSetBuyAmount(userId, stockSymbol, cash, lineNum)

@app.route('/set-buy-amount/', methods=['POST'])
def setBuyAmount():
    try:
        userId = request.form.getlist('userId')[0]
        stockSymbol = request.form.getlist('stockSymbol')[0]
        cash = float(request.form.getlist('cash')[0])
    except:
        print "something went wrong getting data."
        return
    result = doSetBuyAmount(userId, stockSymbol, cash)
    return render_template('result.html', result=result)

# Cancel Set Buy methods
def doCancelSetBuy(userId, stockSymbol, lineNum=0):
    data = {"command": "CANCEL_SET_BUY", "userId": userId, "stockSymbol": stockSymbol, "lineNum": lineNum}
    return sendAndReceive(data)

@app.route('/api/cancel-set-buy/<string:userId>/<string:stockSymbol>/', methods=['POST'])
def apiCancelSetBuy(userId, stockSymbol):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    return doCancelSetBuy(userId, stockSymbol, lineNum)

@app.route('/cancel-set-buy/', methods=['POST'])
def cancelSetBuy():
    try:
        userId = request.form.getlist('userId')[0]
        stockSymbol = request.form.getlist('stockSymbol')[0]
    except:
        print "something went wrong getting data."
        return
    result = doCancelSetBuy(userId, stockSymbol)
    return render_template('result.html', result=result)

# Set Buy Trigger methods
def doSetBuyTrigger(userId, stockSymbol, cash, lineNum=0):
    data = {"command": "SET_BUY_TRIGGER", "userId": userId, "stockSymbol": stockSymbol, "cash": cash, "lineNum": lineNum}
    return sendAndReceive(data)

@app.route('/api/set-buy-trigger/<string:userId>/<string:stockSymbol>/', methods=['POST'])
def apiSetBuyTrigger(userId, stockSymbol):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    try:
        cash = float(request.form['cash'].decode('utf-8'))
    except:
        return "Can't convert cash value to float" , request.form['cash'].decode('utf-8')
    return doSetBuyTrigger(userId, stockSymbol, cash, lineNum)

@app.route('/set-buy-trigger/', methods=['POST'])
def setBuyTrigger():
    try:
        userId = request.form.getlist('userId')[0]
        stockSymbol = request.form.getlist('stockSymbol')[0]
        cash = float(request.form.getlist('cash')[0])
    except:
        print "something went wrong getting data."
        return
    result = doSetBuyTrigger(userId, stockSymbol, cash)
    return render_template('result.html', result=result)

# Set Sell Amount methods
def doSetSellAmount(userId, stockSymbol, cash, lineNum=0):
    data = {"command": "SET_SELL_AMOUNT", "userId": userId, "stockSymbol": stockSymbol, "cash": cash, "lineNum": lineNum}
    return sendAndReceive(data)

@app.route('/api/set-sell-amount/<string:userId>/<string:stockSymbol>/', methods=['POST'])
def apiSetSellAmount(userId, stockSymbol):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    try:
        cash = float(request.form['cash'].decode('utf-8'))
    except:
        return "Can't convert cash value to float" , request.form['cash'].decode('utf-8')
    return doSetSellAmount(userId, stockSymbol, cash, lineNum)

@app.route('/set-sell-amount/', methods=['POST'])
def setSellAmount():
    try:
        userId = request.form.getlist('userId')[0]
        stockSymbol = request.form.getlist('stockSymbol')[0]
        cash = float(request.form.getlist('cash')[0])
    except:
        print "something went wrong getting data."
        return
    result = doSetSellAmount(userId, stockSymbol, cash)
    return render_template('result.html', result=result)

# Set Sell Trigger methods
def doSetSellTrigger(userId, stockSymbol, cash, lineNum=0):
    data = {"command": "SET_SELL_TRIGGER", "userId": userId, "stockSymbol": stockSymbol, "cash": cash,"lineNum": lineNum}
    return sendAndReceive(data)

@app.route('/api/set-sell-trigger/<string:userId>/<string:stockSymbol>/', methods=['POST'])
def apiSetSellTrigger(userId, stockSymbol):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    try:
        cash = float(request.form['cash'].decode('utf-8'))
    except:
        return "Can't convert cash Vvlue to float" , request.form['cash'].decode('utf-8')
    return doSetSellTrigger(userId, stockSymbol, cash, lineNum)

@app.route('/set-sell-trigger/', methods=['POST'])
def setSellTrigger():
    try:
        userId = request.form.getlist('userId')[0]
        stockSymbol = request.form.getlist('stockSymbol')[0]
        cash = float(request.form.getlist('cash')[0])
    except:
        print "something went wrong getting data."
        return
    result = doSetSellTrigger(userId, stockSymbol, cash)
    return render_template('result.html', result=result)

# Cancel Set Sell methods
def doCancelSetSell(userId, stockSymbol, lineNum=0):
    data = {"command": "CANCEL_SET_SELL", "userId": userId, "stockSymbol": stockSymbol, "lineNum": lineNum}
    return sendAndReceive(data)

@app.route('/api/cancel-set-sell/<string:userId>/<string:stockSymbol>/', methods=['POST'])
def apiCancelSetSell(userId, stockSymbol):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    return doCancelSetSell(userId, stockSymbol, lineNum)

@app.route('/cancel-set-sell/', methods=['POST'])
def cancelSetSell():
    try:
        userId = request.form.getlist('userId')[0]
        stockSymbol = request.form.getlist('stockSymbol')[0]
    except:
        print "something went wrong getting data."
        return
    result = doCancelSetSell(userId, stockSymbol)
    return render_template('result.html', result=result)

# Dumplog methods
def doDumplog(userId, lineNum=0):
    data = {"command": "DUMPLOG", "lineNum": lineNum, "userId": userId}
    return sendAndReceive(data)

@app.route('/api/dumplog/', methods=['POST'])
def apiDumpLog():
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    fileName = request.form['fileName']
    return doDumplog(fileName, lineNum)

# Display Summary methods
def doDisplaySummary(userId, lineNum=0):
    data = {"command": "DISPLAY_SUMMARY", "userId": userId, "lineNum": lineNum}
    return sendAndReceive(data)

@app.route('/api/display-summary/<string:userId>/', methods=['GET'])
def apiDisplaySummary(userId):
    lineNum = int(request.form['lineNum'].decode('utf-8'))
    return doDisplaySummary(userId, lineNum)

@app.route('/display-summary/', methods=['GET'])
def displaySummary():
    try:
        userId = request.form.getlist('userId')[0]
    except:
        print "something went wrong getting data."
        return
    result = doDisplaySummary(userId)
    return render_template('result.html', result=result)

if __name__ == '__main__':
    transactionClient = RabbitMQClient(RabbitMQClient.TRANSACTION)
    app.run(host="0.0.0.0",port=44424) 
