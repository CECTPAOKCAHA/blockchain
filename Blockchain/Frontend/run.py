""" from crypt import methods """
from flask import Flask, render_template, request, redirect, url_for
from Blockchain.client.sendBTC import SendBTC 
from Blockchain.Backend.core.Tx import Tx

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/block')
def block():
    return "<h1>Block</h1>"

@app.route('/transactions')
def transactions():
    return "<h1>Transactions</h1>"

@app.route('/mempool')
def mempool():
    return "<h1>Mempool</h1>"

@app.route('/search')
def search():
    return "<h1>Search</h1>"

@app.route('/wallet', methods=["GET", "POST"])

def wallet():
    message = ''
    if request.method == "POST":
        FromAddress = request.form.get("fromAddress")
        ToAddress = request.form.get("toAddress")
        Amount = request.form.get("Amount", type=int)
        sendCoin = SendBTC(FromAddress, ToAddress, Amount, UTXOS)
        TxObj = sendCoin.prepareTransaction()

        scriptPubKey = sendCoin.scriptPubKey(FromAddress)
        verified = True

        if not TxObj:
            message = "Invalid Transaction"

        """In the provided function wallet, the condition if not TxObj: will be true in the following scenarios:

        TxObj is None: If sendCoin.prepareTransaction() returns None, the if not TxObj: condition will evaluate to 
        True because None is considered a falsy value in Python.

        TxObj is an Empty Collection: If TxObj is an empty collection (such as an empty list, dictionary, or set), 
        the condition will also be true because empty collections are considered falsy in Python. For example, if 
        prepareTransaction returns an empty list [], then if not TxObj: will be true.

        TxObj is an Empty String: If TxObj is an empty string '', the condition will be true because empty strings 
        are considered falsy.

        TxObj is Zero: If TxObj is the integer 0, the condition will be true as zero is considered falsy.

        To summarize, the if not TxObj: statement will be true if TxObj evaluates to any of the following falsy 
        values: None, False, 0, '', [], {}, or set(). In the context of this function, the most likely scenario is 
        that TxObj is None if sendCoin.prepareTransaction() fails to create a valid transaction object."""

        if isinstance(TxObj, Tx):
            for index, tx in enumerate(TxObj.tx_ins):
                if not TxObj.verify_input(index, scriptPubKey):
                    verified = False

            if verified:
                MEMPOOL[TxObj.TxId] = TxObj
                message = "Transaction added in memory pool"                                       

    return render_template('wallet.html', message = message)

def main(utxos, MemPool):
    global UTXOS
    global MEMPOOL
    UTXOS = utxos
    MEMPOOL = MemPool
    app.run()


