
# Class for a logging 'server'
# In general, an event takes the form of:
#   event = {
#       'type': 'someType',
#           userCommand
#           accountTransaction
#           systemEvent
#           quoteServer
#           errorEvent            
#       'timestamp': seconds since the epoch,
#       'server': 'where the server originated from',
#       'transactionNum': the transaction number the event is associated with,
#       'username': 'userId of the user who triggered the event'
#       'args': {} Some dictionary - specific for the type of event.
#   }


# NOT TO BE INSTANTIATED
class baseEvent():
	# possible event types
	eventTypes = {
		'userCommandEvent': 'userCommandEvent',
		'accountTransactionEvent': 'accountTransactionEvent',
		'systemEvent': 'systemEvent',
		'quoteServerEvent': 'quoteServerEvent',
		'errorEvent': 'errorEvent'
	}

	__init__(self, timeStamp, server, transactionNum, userId):
		self.eventType = None
		self.timeStamp = timeStamp
		self.server = server
		self.transactionNum = transactionNum
		self.userId = userId

	serialize(self):
		return {
			"eventType": self.eventType,
			"timeStamp": self.timeStamp,
			"server": self.server,
			"transactionNum": self.transactionNum,
			"userId": self.userId
		}

class quoteServerEvent(baseEvent):

	__init__(self, timeStamp, server, transactionNum, userId, quoteServerTime, stockSymbol, price, cryptoKey):
		super(quoteServerEvent, self).__init__(timeStamp, server, transactionNum, userId)
		self.eventType = self.eventTypes['quoteServerEvent']
		self.quoteServerTime = quoteServerTime
		self.stockSymbol = stockSymbol
		self.price = price
		self.cryptoKey = cryptoKey

	serialize(self):
		return super(self).update({
			"quoteServerTime": self.quoteServerTime,
			"stockSymbol": self.stockSymbol,
			"price": self.price,
			"cryptoKey": self.cryptoKey
		})

class accountTransactionEvent(baseEvent):

	accountTransactionEvents = {
		'add': 'add',
		'remove': 'remove',
		'reserve': 'reserve',
		'free': 'free'
	}

	__init__(self, timeStamp, server, transactionNum, userId, accountTransactionEventType, funds):
		super(accountTransactionEvent, self).__init__(timeStamp, server, transactionNum, userId)
		self.eventType = self.eventTypes['accountTransactionEvent']
		self.accountTransactionEventType = self.accountTransactionEvents[accountTransactionEventType]
		self.funds = funds

	serialize(self):
		return super(self).update({
			"accountTransactionEventType": self.accountTransactionEventType,
			"funds": self.funds
		})

class commandEvent(baseEvent):

	__init__(self, eventType, timeStamp, server, transactionNum, userId)
		super(commandEvent, self).__init__(timeStamp, server, transactionNum, userId)

class errorEvent(commandEvent):

class systemEvent(commandEvent):

class userCommand(commandEvent):

#   Valid 'type's and their arg values:
#       userCommand
#           args: {
#               'command': {'name': ,
#                           args{}}'string representing the user's command',
#                   add
#                   commit_buy
#                   cancel_buy
#                   commit_sell
#                   cancel_sell
#                   display_summary
#                       no additional args
#
#                   quote
#                   buy
#                   sell
#                   set_buy_amount
#                   cancel_set_buy
#                   set_buy_trigger
#                   set_sell_amount
#                   set_sell_trigger
#                   cancel_set_sell
#                       need stockSymbol
#
#                   dumplog
#                       fileName
#                    
#                   add
#                   buy
#                   sell
#                   set_buy_amount
#                   set_buy_trigger
#                   set_sell_amount
#                   set_sell_trigger
#                       funds
#           }
#       accountTransaction
#           args: {
#               'action': string corresponding to type of account transaction
#                   add
#                   remove
#                   reserve
#                   free                      
#               'funds': amount of money being moved    
#           }
#       systemEvent
#           args: {
#               'command': same as in userCommand
#           }
#       quoteServer
#           args: {
#               'quoteServerTime': time the quote was received from the quote server,
#               'stockSymbol': 'stcksymbl',
#               'price': price of the stock at the time the server quoted it,
#               'cryptokey': 'cryptographic key the server returns'
#           }
#       errorEvent
#           args: {
#               'command': same as in userCommand,
#               'errorMessage': message associated with the error
#           }
'''
class errorEvent:
	__init__(self, eventType, timeStamp, server, transactionNum, userid):
		self.eventType: eventType,
#   		userCommand
#           accountTransaction
#           systemEvent
#           quoteServer
#           errorEvent  
		self.timeStamp: timeStamp,
		self.server: server,
		self.transactionNum: transactionNum,
		self.username: userId,
		self.args = {}
          
#       'timestamp': seconds since the epoch,
#       'server': 'where the server originated from',
#       'transactionNum': the transaction number the event is associated with,
#       'username': 'userId of the user who triggered the event'
#       'args': {} Some dictionary - specific for the type of event.
    systemEvent
    accountTransaction
    commandEvent - this adds a method for each type of command
        userCommand
        quoteServer
        errorEvent

method add arguments
'''