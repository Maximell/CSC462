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

'''
COMMIT_BUY: userid
CANCEL_BUY: userid
SELL: userid, StockSymbol, amount
COMMIT_SELL: userid
CANCEL_SELL: userid
SET_BUY_AMOUNT: userid, StockSymbol, amount
CANCEL_SET_BUY: userid, StockSymbol
SET_BUY_TRIGGER: userid, StockSymbol, amount
SET_SELL_AMOUNT: userid, StockSymbol, amount
SET_SELL_TRIGGER: userid, StockSymbol, amount
CANCEL_SET_SELL: userid, StockSymbol
DUMPLOG: filename
DISPLAY_SUMMARY: userid
'''