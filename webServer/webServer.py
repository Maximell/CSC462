from flask import Flask
from flask import request
import json
import pika
app = Flask(__name__)

def sendtoQueue(data):
	connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
	channel = connection.channel()
	channel.queue_declare(queue='webserverIn')
	channel.basic_publish(exchange='', routing_key='webserverIn', body=data)
	connection.close


@app.route('/')
def hello_world():
	return 'Hello, world.'

@app.route('/add/<string:userId>/', methods=['POST'])
def add(userId):
	amount = float(request.form['amount'].decode('utf-8'))
	data = json.dumps({"userId":userId, "amount":amount })
	sendtoQueue(data)
	return 'Trying to add %f amount to user %s.' % (amount, userId)

@app.route('/quote/<string:userId>/<string:stockSymbol>/', methods=['GET'])
def quote(userId, stockSymbol):
	return 'Getting a quote for user %s on stock %s.' % (userId, stockSymbol)

@app.route('/buy/<string:userId>/<string:stockSymbol>/', methods=['POST'])
def buy(userId, stockSymbol):
	amount = float(request.form['amount'].decode('utf-8'))

	return 'Buying stock %s for user %s for amount %f' % (stockSymbol, userId, amount)

@app.route('/commit-buy/<string:userId>/', methods=['POST'])
def commitBuy(userId):
	return 'Committing buy for user %s.' % (userId)

@app.route('/cancel-buy/<string:userId>/', methods=['POST'])
def cancelBuy(userId):
	return 'Cancelling buy for user %s.' % (userId)

@app.route('/sell/<string:userId>/<string:stockSymbol>/', methods=['POST'])
def sell(userId, stockSymbol):
	amount = float(request.form['amount'].decode('utf-8'))
	print amount
	return 'Selling %f of stock %s for user %s' % (amount, stockSymbol, userId)

@app.route('/commit-sell/<string:userId>/', methods=['POST'])
def commitSell(userId):
	return 'Committing sell for user %s.' % (userId)

@app.route('/cancel-sell/<string:userId>/', methods=['POST'])
def cancelSell(userId):
	return 'Cancelling sell for user %s.' % (userId)

@app.route('/set-buy-amount/<string:userId>/<string:stockSymbol>/', methods=['POST'])
def setBuyAmount(userId, stockSymbol):
	amount = float(request.form['amount'].decode('utf-8'))
	# print "Canceling Set buy"
	return 'Setting buy of $%f on stock %s for user %s.' % (amount, stockSymbol, userId)

@app.route('/cancel-set-buy/<string:userId>/<string:stockSymbol>/', methods=['POST'])
def cancelSetBuy(userId, stockSymbol):
	return 'Cancelling set buy for user %s on stock %s.' % (userId, stockSymbol)

@app.route('/set-buy-trigger/<string:userId>/<string:stockSymbol>/', methods=['POST'])
def setBuyTrigger(userId, stockSymbol):
	amount = float(request.form['amount'].decode('utf-8'))

	return 'Setting a buy trigger for user %s on stock %s for amount %f.' % (userId, stockSymbol, amount)

@app.route('/set-sell-amount/<string:userId>/<string:stockSymbol>/', methods=['POST'])
def setSellAmount(userId, stockSymbol):
	amount = float(request.form['amount'].decode('utf-8'))

	return 'Setting a sell for user %s on stock %s for amount %f.' % (userId, stockSymbol, amount)

@app.route('/set-sell-trigger/<string:userId>/<string:stockSymbol>/', methods=['POST'])
def setSellTrigger(userId, stockSymbol):
	amount = float(request.form['amount'].decode('utf-8'))

	return 'Setting a sell trigger for user %s on stock %s for amount %f.' % (userId, stockSymbol, amount)

@app.route('/cancel-set-sell/<string:userId>/<string:stockSymbol>/', methods=['POST'])
def cancelSetSell(userId, stockSymbol):
	return 'Cancelling set sell for user %s on stock %s.' % (userId, stockSymbol)

@app.route('/dumplog/', methods=['POST'])
def dumpLog():
	fileName = request.form['fileName']
	# print "dumplog"
	return 'Dumping log into file: %s.' % (fileName)


@app.route('/display-summary/<string:userId>/', methods=['GET'])
def displaySummary(userId):
	return 'Displaying summary for user %s.' % (userId)

if __name__ == '__main__':
    app.run()
