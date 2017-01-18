from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
	return 'Hello, world.'

@app.route('/add/<string:userId>/<float:amount>')
@app.route('/add/<string:userId>/<int:amount>')
def add(userId, amount):
	return 'Trying to add %f amount to user %s.' % (amount, userId)

@app.route('/quote/<string:userId>/<string:stockSymbol>')
def quote(userId, stockSymbol):
	return 'Getting a quote for user %s on stock %s.' % (userId, stockSymbol)

@app.route('/buy/<string:userId>/<string:stockSymbol>/<float:amount>')
@app.route('/buy/<string:userId>/<string:stockSymbol>/<int:amount>')
def buy(userId, stockSymbol, amount):
	return 'Buying stock %s for user %s for amount %f' % (stockSymbol, userId, amount)

@app.route('/commit-buy/<string:userId>')
def commitBuy(userId):
	return 'Committing buy for user %s.' % (userId)

@app.route('/cancel-buy/<string:userId')
def cancelBuy(userId):
	return 'Cancelling buy for user %s.' % (userId)

@app.route('/sell/<string:userId>/<string:stockSymbol>/<float:amount>')
@app.route('/sell/<string:userId>/<string:stockSymbol>/<int:amount>')
def sell(userId, stockSymbol, amount):
	return 'Selling %f of stock %s for user %s' % (amount, stockSymbol, userId)

@app.route('/commit-sell/<string:userId>')
def commitSell(userId):
	return 'Committing sell for user %s.' % (userId)

@app.route('/cancel-sell/<string:userId')
def cancelSell(userId):
	return 'Cancelling sell for user %s.' % (userId)

@app.route('/set-buy-amount/<string:userId>/<string:stockSymbol>/<float:amount>')
@app.route('/set-buy-amount/<string:userId>/<string:stockSymbol>/<int:amount>')
def setBuyAmount(userId, stockSymbol, amount):
	return 'Setting buy of $%f on stock %s for user %s.' % (amount, stockSymbol, userId)

@app.route('/cancel-set-buy/<string:userId>/<string:stockSymbol>')
def cancelSetBuy(userId, stockSymbol):
	return 'Cancelling set buy for user %s on stock %s.' % (userId, stockSymbol)

@app.route('/set-buy-trigger/<string:userId>/<string:stockSymbol>/<float:amount>')
@app.route('/set-buy-trigger/<string:userId>/<string:stockSymbol>/<int:amount>')
def setBuyTrigger(userId, stockSymbol, amount):
	return 'Setting a buy trigger for user %s on stock %s for amount %f.' % (userId, stockSymbol, amount)

@app.route('/set-sell-amount/<string:userId>/<string:stockSymbol>/<float:amount>')
@app.route('/set-sell-amount/<string:userId>/<string:stockSymbol>/<int:amount>')
def setSellAmount(userId, stockSymbol, amount):
	return 'Setting a sell for user %s on stock %s for amount %f.' % (userId, stockSymbol, amount)

@app.route('/set-sell-trigger/<string:userId>/<string:stockSymbol>/<float:amount>')
@app.route('/set-sell-trigger/<string:userId>/<string:stockSymbol>/<int:amount>')
def setSellTrigger(userId, stockSymbol, amount):
	return 'Setting a sell trigger for user %s on stock %s for amount %f.' % (userId, stockSymbol, amount)

@app.route('/cancel-set-sell/<string:userId>/<string:stockSymbol>')
def cancelSetSell(userId, stockSymbol):
	return 'Cancelling set sell for user %s on stock %s.' % (userId, stockSymbol)

@app.route('/dumplog/<string:fileName>')
def dumpLog(fileName):
	return 'Dumping log into file: %s.' % (fileName)

@app.route('/display-summary/<string:userId>')
def displaySummary(userId):
	return 'Displaying summary for user %s.' % (userId)
