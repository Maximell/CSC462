
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
		'userCommand': 'userCommand',
		'accountTransaction': 'accountTransaction',
		'systemEvent': 'systemEvent',
		'quoteServer': 'quoteServer',
		'errorEvent': 'errorEvent'
	}

	__init__(self, timeStamp, server, transactionNum, userId):
		self.eventType = None
		self.timeStamp = timeStamp
		self.server = server
		self.transactionNum = transactionNum
		self.userId = userId

class quoteServer(baseEvent):

	__init__(self, timeStamp, server, transactionNum, userId, quoteServerTime, stockSymbol, price, cryptoKey):
		super(quoteServer, self).__init__(timeStamp, server, transactionNum, userId)
		self.eventType = self.eventTypes['quoteServer']
		self.quoteServerTime = quoteServerTime
		self.stockSymbol = stockSymbol
		self.price = price
		self.cryptoKey = cryptoKey



class errorEvent(baseEvent):

	__init__(self, eventType, timeStamp, server, transactionNum, userId, )
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