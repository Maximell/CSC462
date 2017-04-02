import os
import time
import json
import pika
import random
from flask import Flask, request, render_template, url_for, redirect
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_login import logout_user
from flask_user import login_required, current_user, UserManager, UserMixin, SQLAlchemyAdapter
from rabbitMQSetups import RabbitMQClient, RabbitMQReceiver

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

app = Flask(__name__)

class ConfigClass(object):
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'THIS IS AN INSECURE SECRET')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///basic_app.sqlite')

    # Flask-Mail settings
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', 'seng462group22017@gmail.com')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', 'group2Password')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', '"group2App" <noreply@seng462group2App.com>')
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', '465'))
    MAIL_USE_SSL = int(os.getenv('MAIL_USE_SSL', True))

    # Flask-User settings
    USER_APP_NAME = "AppName"

# Setup Flask app and app.config
app = Flask(__name__)
app.config.from_object(__name__+'.ConfigClass')

# Initialize Flask extensions
db = SQLAlchemy(app)
mail = Mail(app)

# Define the User data model.
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)

    # User authentication infromation
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False, server_default='')

    # User email information
    email = db.Column(db.String(255), nullable=False, unique=True)
    confirmed_at = db.Column(db.DateTime())

    # User information
    active  = db.Column('is_active', db.Boolean(), nullable=False, server_default='0')
    first_name = db.Column(db.String(100), nullable=False, server_default='')
    last_name = db.Column(db.String(100), nullable=False, server_default='')

# Create all database tables
db.create_all()

# Setup Flask-User
db_adapter = SQLAlchemyAdapter(db, User) # Register the User Model
user_manager = UserManager(db_adapter, app) # Initialize Flask-User


#Home
@app.route('/', methods=['GET'])
@login_required
def index():
    return render_template('index.html')

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Add methods
def doAdd(userId, cash, lineNum):
    data = {"command": "ADD", "userId": userId, "cash": cash, "lineNum": lineNum}
    return sendAndReceive(data)

@app.route('/add/', methods=['POST'])
@login_required
def add():
    try:
        userId = current_user.id
        cash = float(request.form.getlist("cash")[0])
    except:
        print "something went wrong parsing the data."
        return "something went wrong parsing the data."
    result = doAdd(userId, cash, getRandomRequestLineNum())
    return render_template('result.html', result=result)

# Quote methods
def doQuote(userId, stockSumbol, lineNum):
    data = {"command": "QUOTE", "userId": userId, "stockSymbol": stockSumbol, "lineNum": lineNum}
    return sendAndReceive(data)

@app.route('/quote/', methods=['GET', 'POST'])
@login_required
def quote():
    try:
        userId = current_user.id
        stockSymbol = request.form.getlist('stockSymbol')[0]
    except:
        print "something went wrong parsing the data."
        return "something went wrong parsing the data."
    result = doQuote(userId, stockSymbol, getRandomRequestLineNum())
    return render_template('result.html', result=result)

# Buy methods
def doBuy(userId, stockSymbol, cash, lineNum):
    data = {"command": "BUY", "userId": userId, "stockSymbol": stockSymbol, "cash": cash, "lineNum": lineNum}
    return sendAndReceive(data)

@app.route('/buy/', methods=['POST'])
@login_required
def buy():
    try:
        userId = current_user.id
        stockSymbol = request.form.getlist('stockSymbol')[0]
        cash = float(request.form.getlist('cash')[0])
    except:
        print "something went wrong parsing the data."
        return "something went wrong parsing the data."
    result = doBuy(userId, stockSymbol, cash, getRandomRequestLineNum())
    return render_template('result.html', result=result)

# Commit Buy methods
def doCommitBuy(userId, lineNum):
    data = {"command": "COMMIT_BUY", "userId": userId, "lineNum": lineNum}
    return sendAndReceive(data)

@app.route('/commit-buy/', methods=['POST'])
@login_required
def commitBuy():
    try:
        userId = current_user.id
    except:
        print "something went wrong parsing the data."
        return "something went wrong parsing the data."
    result = doCommitBuy(userId, getRandomRequestLineNum())
    return render_template('result.html', result=result)

# Cancel Buy methods
def doCancelBuy(userId, lineNum):
    data = {"command": "CANCEL_BUY", "userId": userId, "lineNum": lineNum}
    return sendAndReceive(data)

@app.route('/cancel-buy/', methods=['POST'])
@login_required
def cancelBuy():
    try:
        userId = current_user.id
    except:
        print "something went wrong parsing the data."
        return "something went wrong parsing the data."
    result = doCommitBuy(userId, getRandomRequestLineNum())
    return render_template('result.html', result=result)

# Sell methods
def doSell(userId, stockSymbol, cash, lineNum):
    data = {"command": "SELL", "userId": userId, "stockSymbol": stockSymbol, "cash": cash, "lineNum": lineNum}
    return sendAndReceive(data)

@app.route('/sell/', methods=['POST'])
@login_required
def sell():
    try:
        userId = current_user.id
        stockSymbol = request.form.getlist('stockSymbol')[0]
        cash = float(request.form.getlist('cash')[0])
    except:
        print "something went wrong parsing the data."
        return "something went wrong parsing the data."
    result = doSell(userId, stockSymbol, cash, getRandomRequestLineNum())
    return render_template('result.html', result=result)

# Commit Sell methods
def doCommitSell(userId, lineNum=0):
    data = {"command": "COMMIT_SELL", "userId": userId, "lineNum": lineNum}
    return sendAndReceive(data)

@app.route('/commit-sell/', methods=['POST'])
@login_required
def commitSell():
    try:
        userId = current_user.id
    except:
        print "something went wrong parsing the data."
        return "something went wrong parsing the data."
    result = doCommitSell(userId)
    return render_template('result.html', result=result)

# Cancel Sell methods
def doCancelSell(userId, lineNum):
    data = {"command": "CANCEL_SELL", "userId": userId, "lineNum": lineNum}
    return sendAndReceive(data)

@app.route('/cancel-sell/', methods=['POST'])
@login_required
def cancelSell():
    try:
        userId = current_user.id
    except:
        print "something went wrong parsing the data."
        return "something went wrong parsing the data."
    result = doCommitSell(userId, getRandomRequestLineNum())
    return render_template('result.html', result=result)

# Set Buy Amount methods
def doSetBuyAmount(userId, stockSymbol, cash, lineNum):
    data = {"command": "SET_BUY_AMOUNT", "userId": userId, "stockSymbol": stockSymbol, "cash": cash, "lineNum": lineNum}
    return sendAndReceive(data)

@app.route('/set-buy-amount/', methods=['POST'])
@login_required
def setBuyAmount():
    try:
        userId = current_user.id
        stockSymbol = request.form.getlist('stockSymbol')[0]
        cash = float(request.form.getlist('cash')[0])
    except:
        print "something went wrong parsing the data."
        return "something went wrong parsing the data."
    result = doSetBuyAmount(userId, stockSymbol, cash, getRandomRequestLineNum())
    return render_template('result.html', result=result)

# Cancel Set Buy methods
def doCancelSetBuy(userId, stockSymbol, lineNum):
    data = {"command": "CANCEL_SET_BUY", "userId": userId, "stockSymbol": stockSymbol, "lineNum": lineNum}
    return sendAndReceive(data)

@app.route('/cancel-set-buy/', methods=['POST'])
@login_required
def cancelSetBuy():
    try:
        userId = current_user.id
        stockSymbol = request.form.getlist('stockSymbol')[0]
    except:
        print "something went wrong parsing the data."
        return "something went wrong parsing the data."
    result = doCancelSetBuy(userId, stockSymbol, getRandomRequestLineNum())
    return render_template('result.html', result=result)

# Set Buy Trigger methods
def doSetBuyTrigger(userId, stockSymbol, cash, lineNum):
    data = {"command": "SET_BUY_TRIGGER", "userId": userId, "stockSymbol": stockSymbol, "cash": cash, "lineNum": lineNum}
    return sendAndReceive(data)

@app.route('/set-buy-trigger/', methods=['POST'])
@login_required
def setBuyTrigger():
    try:
        userId = current_user.id
        stockSymbol = request.form.getlist('stockSymbol')[0]
        cash = float(request.form.getlist('cash')[0])
    except:
        print "something went wrong parsing the data."
        return "something went wrong parsing the data."
    result = doSetBuyTrigger(userId, stockSymbol, cash, getRandomRequestLineNum())
    return render_template('result.html', result=result)

# Set Sell Amount methods
def doSetSellAmount(userId, stockSymbol, cash, lineNum):
    data = {"command": "SET_SELL_AMOUNT", "userId": userId, "stockSymbol": stockSymbol, "cash": cash, "lineNum": lineNum}
    return sendAndReceive(data)

@app.route('/set-sell-amount/', methods=['POST'])
@login_required
def setSellAmount():
    try:
        userId = current_user.id
        stockSymbol = request.form.getlist('stockSymbol')[0]
        cash = float(request.form.getlist('cash')[0])
    except:
        print "something went wrong parsing the data."
        return "something went wrong parsing the data."
    result = doSetSellAmount(userId, stockSymbol, cash, getRandomRequestLineNum())
    return render_template('result.html', result=result)

# Set Sell Trigger methods
def doSetSellTrigger(userId, stockSymbol, cash, lineNum):
    data = {"command": "SET_SELL_TRIGGER", "userId": userId, "stockSymbol": stockSymbol, "cash": cash,"lineNum": lineNum}
    return sendAndReceive(data)

@app.route('/set-sell-trigger/', methods=['POST'])
@login_required
def setSellTrigger():
    try:
        userId = current_user.id
        stockSymbol = request.form.getlist('stockSymbol')[0]
        cash = float(request.form.getlist('cash')[0])
    except:
        print "something went wrong parsing the data."
        return "something went wrong parsing the data."
    result = doSetSellTrigger(userId, stockSymbol, cash, getRandomRequestLineNum())
    return render_template('result.html', result=result)

# Cancel Set Sell methods
def doCancelSetSell(userId, stockSymbol, lineNum):
    data = {"command": "CANCEL_SET_SELL", "userId": userId, "stockSymbol": stockSymbol, "lineNum": lineNum}
    return sendAndReceive(data)

@app.route('/cancel-set-sell/', methods=['POST'])
@login_required
def cancelSetSell():
    try:
        userId = current_user.id
        stockSymbol = request.form.getlist('stockSymbol')[0]
    except:
        print "something went wrong parsing the data."
        return "something went wrong parsing the data."
    result = doCancelSetSell(userId, stockSymbol, getRandomRequestLineNum())
    return render_template('result.html', result=result)

# Dumplog methods
def doDumplog(userId, lineNum):
    data = {"command": "DUMPLOG", "lineNum": lineNum, "userId": userId}
    return sendAndReceive(data)

@app.route('/dumplog/', methods=['POST'])
@login_required
def apiDumpLog():
    fileName = request.form['fileName']
    return doDumplog(fileName, getRandomRequestLineNum())

# Display Summary methods
def doDisplaySummary(userId, lineNum):
    data = {"command": "DISPLAY_SUMMARY", "userId": userId, "lineNum": lineNum}
    return sendAndReceive(data)

@app.route('/display-summary/', methods=['GET'])
@login_required
def displaySummary():
    try:
        userId = current_user.id
    except:
        print "something went wrong parsing the data."
        return "something went wrong parsing the data."
    result = doDisplaySummary(userId, getRandomRequestLineNum())
    return render_template('result.html', result=result)


if __name__ == '__main__':
    transactionClient = RabbitMQClient(RabbitMQClient.TRANSACTION)
    app.run(host="0.0.0.0",port=44424)
