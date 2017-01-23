
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

class Event(object):
	# possible event types
	eventTypes = {
		'userCommandEvent': 'userCommandEvent',
		'accountTransactionEvent': 'accountTransactionEvent',
		'systemEvent': 'systemEvent',
		'quoteServerEvent': 'quoteServerEvent',
		'errorEvent': 'errorEvent'
	}

	def __init__(self, **kwargs):
		# get base event kwargs
		self.eventType = kwargs['eventType']
		self.timeStamp = kwargs['timeStamp']
		self.server = kwargs['server']
		self.transactionNum = kwargs['transactionNum']
		self.userId = kwargs['userId']
		# handle the other kwargs
		self._handleKwargs(**kwargs)
		
	def _handleKwargs(self, **kwargs):
		# figure out what type of event we are dealing with
		if self.eventType == 'userCommandEvent':
			self._handleUserCommandEventKwargs(**kwargs)
		elif self.eventType == 'accountTransactionEvent':
			self._handleAccountTransactionEventKwargs(**kwargs)
		elif self.eventType == 'systemEvent':
			self._handleSystemEventKwargs(**kwargs)
		elif self.eventType == 'quoteServerEvent':
			self._handleQuoteServerEventKwargs(**kwargs)
		elif self.eventType == 'errorEvent'
			self._handleErrorEventKwargs(**kwargs)

		# switch statements for each type of eventType
			# for each eventType, have a handleEVENTTYPEkwargs method - call it.
	def _handleUserCommandEventKwargs(**kwargs):
		self._handleCommandKwargs(**kwargs)

		return
	
	def _handleAccountTransactionEventKwargs(self, **kwargs):
		self.accountTransactionEventType = self.accountTransactionEvents[kwargs['AccountTransactionEventType']]
		self.funds = kwargs['funds']

	def _handleSystemEventKwargs(self, **kwargs):
		return

	def _handleQuoteServerEventKwargs(self, **kwargs):
		self.quoteServerTime = kwargs['quoteServerTime']
		self.stockSymbol = kwargs['stockSymbol']
		self.price = kwargs['price']
		self.cryptoKey = kwargs['cryptoKey']

	
	def _handleErrorEventKwargs(self, **kwargs):
		self.errorMessage = kwargs['errorMessage']
		self._handleCommandKwargs(**kwargs)

	def _handleCommandKwargs(self, **kwargs):
		self.commandName = kwargs['commandName']
		
		if commandName in ['quote', 'cancel_set_buy', 'cancel_set_sell']:
			self.stockSymbol = kwargs['stockSymbol']
		elif commandName in ['dumplog']:
			self.fileName = kwargs['fileName']
		elif commandName in ['add']:
			self.amount = kwargs['amount']
		elif commandName in ['buy', 'sell', 'set_buy_amount', 'set_sell_amount', 'set_buy_trigger', 'set_sell_trigger']:
			self.amount = kwargs['amount']
			self.stockSymbol = kwargs['stockSymbol']
		elif commandName in ['commit_buy', 'cancel_buy', 'commit_sell', 'cancel_sell', 'display_summary']:
			# nothing to be added for these commands
			return

	def serialize(self):
		baseSerialization = {
			'eventType': self.eventType,
			'timeStamp': self.timeStamp,
			'server': self.server,
			'transactionNum': self.transactionNum,
			'userId': self.userId
		}
		# for each diff type of eventType, extend the base serialization.
		self._handleKwargsSerialization(**kwargs)

	def _handleKwargsSerialization(self, **kwargs):
		# for each type of event handle the serialization
		return


class QuoteServerEvent(BaseEvent):

	def __init__(self, timeStamp, server, transactionNum, userId, **kwargs):	
		super(QuoteServerEvent, self).__init__(timeStamp, server, transactionNum, userId, **kwargs)
		self.eventType = self.eventTypes['QuoteServerEvent']

		
	def _handleKwargs(self, **kwargs):
		self.quoteServerTime = kwargs['quoteServerTime']
		self.stockSymbol = kwargs['stockSymbol']
		self.price = kwargs['price']
		self.cryptoKey = kwargs['cryptoKey']

	def serialize(self):
		return dict(super(QuoteServerEvent, self).serialize(), 
			quoteServerTime=self.quoteServerTime, 
			stockSymbol=self.stockSymbol, 
			price=self.price, 
			cryptoKey=self.cryptoKey
		)

class AccountTransactionEvent(BaseEvent):

	accountTransactionEvents = {
		'add': 'add',
		'remove': 'remove',
		'reserve': 'reserve',
		'free': 'free'
	}

	def __init__(self, timeStamp, server, transactionNum, userId, **kwargs):
		super(AccountTransactionEvent, self).__init__(timeStamp, server, transactionNum, userId)
		self.eventType = self.eventTypes['AccountTransactionEvent']

	def _handleKwargs(self, **kwargs):
		self.accountTransactionEventType = self.accountTransactionEvents[AccountTransactionEventType]
		self.funds = funds

	def serialize(self):
		return dict(super(AccountTransactionEvent, self).serialize(),
			accountTransactionEventType=self.accountTransactionEventType,
			funds=self.funds
		)

class commandEvent(BaseEvent):

	def __init__(self, eventType, timeStamp, server, transactionNum, userId):
		super(commandEvent, self).__init__(timeStamp, server, transactionNum, userId)

	def command(**kwargs):
		commandName = kwargs['name']
		if commandName in ['commit_buy', 'cancel_buy', 'commit_sell', 'cancel_sell', 'display_summary']:
			print 'handle the case where no additional args are needed'
		if commandName in ['quote', 'cancel_set_buy', 'cancel_set_sell']:
			print 'handle the case where stockSymbol is needed'
		if commandName in ['dumplog']:
			print 'handle the case where fileName is needed'
		if commandName in ['add']:
			print 'handle the case where amount is needed'
		if commandName in ['buy', 'sell', 'set_buy_amount', 'set_sell_amount', 'set_buy_trigger', 'set_sell_trigger']:
			print 'handle the case where both amount and stockSymbol are needed'

#   Valid 'type's and their arg values:
#       userCommand
#           args: {
#               'command': {'name': ,
#                           args{}}'string representing the user's command',
#                   commit_buy
#                   cancel_buy
#                   commit_sell
#                   cancel_sell
#                   display_summary
#                       no additional args
#
#                   quote
#                   cancel_set_buy
#                   cancel_set_sell
#                       stockSymbol
#
#                   dumplog
#                       fileName
#                    
#                   add
#                       funds
#
#					buy
#					sell
#					set_buy_amount
#					set_sell_amount
#					set_buy_trigger
#					set_sell_trigger
#						stockSymbol
#						funds
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