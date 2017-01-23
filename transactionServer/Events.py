
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
#       SOME ADDITIONAL ARGS
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

	accountTransactionEvents = {
		'add': 'add',
		'remove': 'remove',
		'reserve': 'reserve',
		'free': 'free'
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

	def _handleUserCommandEventKwargs(**kwargs):
		self._handleCommandKwargs(**kwargs)
	
	def _handleAccountTransactionEventKwargs(self, **kwargs):
		self.accountTransactionEventType = self.accountTransactionEvents[kwargs['AccountTransactionEventType']]
		self.funds = kwargs['funds']

	def _handleSystemEventKwargs(self, **kwargs):
		self._handleCommandKwargs(**kwargs)

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
		if self.commandName in ['quote', 'cancel_set_buy', 'cancel_set_sell']:
			self.stockSymbol = kwargs['stockSymbol']
		elif self.commandName in ['dumplog']:
			self.fileName = kwargs['fileName']
		elif self.commandName in ['add']:
			self.amount = kwargs['amount']
		elif self.commandName in ['buy', 'sell', 'set_buy_amount', 'set_sell_amount', 'set_buy_trigger', 'set_sell_trigger']:
			self.amount = kwargs['amount']
			self.stockSymbol = kwargs['stockSymbol']
		elif self.commandName in ['commit_buy', 'cancel_buy', 'commit_sell', 'cancel_sell', 'display_summary']:
			pass

	def serialize(self):
		# for each diff type of eventType, extend the base serialization.
		return dict(self._handleKwargsSerialization(),
			eventType=self.eventType,
			timeStamp=self.timeStamp,
			server=self.server,
			transactionNum=self.transactionNum,
			userId=self.userId
		}


	def _handleKwargsSerialization(self):
		# for each type of event handle the serialization
		# figure out what type of event we are dealing with
		if self.eventType == 'userCommandEvent':
			return self._handleUserCommandEventKwargsSerialization()
		elif self.eventType == 'accountTransactionEvent':
			return self._handleAccountTransactionEventKwargsSerialization()
		elif self.eventType == 'systemEvent':
			return self._handleSystemEventKwargsSerialization()
		elif self.eventType == 'quoteServerEvent':
			return self._handleQuoteServerEventKwargsSerialization()
		elif self.eventType == 'errorEvent'
			return self._handleErrorEventKwargsSerialization()

	def _handleUserCommandEventKwargsSerialization(self):
		return self._handleCommandSerialization()

	def _handleAccountTransactionEventKwargsSerialization(self):
		return {
			'accountTransactionEventType' = self.accountTransactionEventType,
			'funds' = self.funds
		}

	def _handleSystemEventKwargsSerialization(self):
		return self._handleCommandSerialization()

	def _handleQuoteServerEventKwargsSerialization(self):
		return {
			'quoteServerTime': self.quoteServerTime,
			'stockSymbol': self.stockSymbol,
			'price': self.price,
			'cryptoKey': self.cryptoKey
		}

	def _handleErrorEventKwargsSerialization(self, **kwargs):
		return dict(self._handleCommandSerialization(), {
			'errorMessage': self.errorMessage
		})

	def _handleCommandSerialization(self):
		if self.commandName in ['quote', 'cancel_set_buy', 'cancel_set_sell']:
			return {
				'stockSymbol': self.stockSymbol
			}
		elif self.commandName in ['dumplog']:
			return {
				'fileName': self.fileName
			}
		elif self.commandName in ['add']:
			return {
				'amount': self.amount
			}
		elif self.commandName in ['buy', 'sell', 'set_buy_amount', 'set_sell_amount', 'set_buy_trigger', 'set_sell_trigger']:
			return {
				'amount': self.amount,
				'stockSymbol': self.stockSymbol
			}
		elif self.commandName in ['commit_buy', 'cancel_buy', 'commit_sell', 'cancel_sell', 'display_summary']:
			return {}

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