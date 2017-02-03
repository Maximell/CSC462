# library imports
import requests
from flask import Flask

from OpenSSL import SSL
context = SSL.Context(SSL.SSLv23_METHOD)
# server.pem's location (containing the server private key and the server certificate).
fpem = "cert.pem"
context.use_privatekey_file(fpem)
context.use_certificate_file(fpem)

app = Flask(__name__)

@app.route('/')
def index():
    return 'Flask is running!'

if __name__ == '__main__':
    app.run(host='127.0.0.1', debug=True, ssl_context=context)