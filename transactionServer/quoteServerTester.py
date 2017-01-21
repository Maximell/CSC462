from transactionServer import quotes
import time

quotes = quotes(testing=True, cacheExpire=2)

print "TEST: NO CACHE\n", quotes.getQuote("hello", "usr"), "\n"
print "TEST: CACHE\n", quotes.getQuote("hello", "usr"), "\n"
print "TEST: NO CACHE\n", quotes.getQuoteNoCache("hello", "usr"), "\n"

time.sleep(5) # delays for 5 seconds

print "TEST: EXPIRED CACHE\n", quotes.getQuote("hello", "usr"), "\n"
print "TEST: CACHE\n", quotes.getQuote("hello", "usr"), "\n"

