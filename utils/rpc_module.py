import json, requests
from utils import parsing

class Rpc:
    def __init__(self):
        config = parsing.parse_json('config.json')["rpc"]
        self.recipients = {}

        self.rpc_host = config["rpc_host"]
        self.rpc_port = config["rpc_port"]
        self.rpc_user = config["rpc_user"]
        self.rpc_pass = config["rpc_pass"]
        self.serverURL = 'http://' + self.rpc_host + ':' + self.rpc_port
        self.headers = {'content-type': 'application/json'}

    def addParticipant(self, address, amount):
        '''
        Add participants of the airdrop into self.recipients
        '''
        self.recipients[address] = amount

    def clearRecipients(self):
        '''
        clear participants of the airdrop from self.recipients. Only call once payment has been made
        '''
        self.recipients.clear()

    def total_recipients(self):
        return len(self.recipients)

    def sendmany(self):
        '''
        Send from airdrop wallet specified in config.json
        '''

        payload = json.dumps({"method": "sendmany", "params": ['', self.recipients, 16], "jsonrpc": "2.0"})
        response = requests.post(self.serverURL, headers=self.headers, data=payload,
                                auth=(self.rpc_user, self.rpc_pass))
        return response.json()['result']

    def getinfo(self):
        payload = json.dumps({"method": "getblockchaininfo", "params": [], "jsonrpc": "2.0"})
        response = requests.post(self.serverURL, headers=self.headers, data=payload,
                                auth=(self.rpc_user, self.rpc_pass))
        return response.json()['result']

    def listreceivedbyaddess(self, minconf, includeempty = False, includeWatchOnly = False):
        payload = json.dumps({"method": "listreceivedbyaddress", "params": [minconf, includeempty, includeWatchOnly], "jsonrpc": "2.0"})
        response = requests.post(self.serverURL, headers=self.headers, data=payload,
                                auth=(self.rpc_user, self.rpc_pass))
        return response.json()['result']

    def getnewaddress(self, account):
        payload = json.dumps({"method": "getnewaddress", "params": [account], "jsonrpc": "2.0"})
        response = requests.post(self.serverURL, headers=self.headers, data=payload,
                                auth=(self.rpc_user, self.rpc_pass))
        return response.json()['result']

    def lastWalletTx(self):
        last_confirmed_tx_position = len(self.listtransactions_all()) - 1
        return self.listtransactions_all()[last_confirmed_tx_position]

    def lastTxId(self):
        last_confirmed_tx_position = len(self.listtransactions_all()) - 1
        return self.listtransactions_all()[last_confirmed_tx_position]['txid']

    def listtransactions(self, params, count):
        payload = json.dumps({"method": "listtransactions", "params": [params, count], "jsonrpc": "2.0"})
        response = requests.post(self.serverURL, headers=self.headers, data=payload,
                                auth=(self.rpc_user, self.rpc_pass))
        return response.json()['result']

    def listtransactions_all(self):
        payload = json.dumps({"method": "listtransactions","params": [], "jsonrpc": "2.0"})
        response = requests.post(self.serverURL, headers=self.headers, data=payload,
                                auth=(self.rpc_user, self.rpc_pass))
        return response.json()['result']
    
    def getconnectioncount(self):
        payload = json.dumps({"method": "getconnectioncount", "params": [], "jsonrpc": "2.0"})
        response = requests.post(self.serverURL, headers=self.headers, data=payload,
                               auth=(self.rpc_user, self.rpc_pass))
        return response.json()['result']

    ### work to be done
    def getbalance(self):
        payload = json.dumps({"method": "getbalance", "params": [], "jsonrpc": "2.0"})
        response = requests.post(self.serverURL, headers=self.headers, data=payload,
                                auth=(self.rpc_user, self.rpc_pass))
        return response.json()['result']
    ###################

    def validateaddress(self, params):
        payload = json.dumps({"method": "validateaddress", "params": [params], "jsonrpc": "2.0"})
        response = requests.post(self.serverURL, headers=self.headers, data=payload,
                                auth=(self.rpc_user, self.rpc_pass))
        return response.json()['result']

    def sendtoaddress(self, address, amount):
        payload = json.dumps({"method": "sendtoaddress", "params": [address, "%.2f" % round(amount, 4)], "jsonrpc": "2.0"})
        response = requests.post(self.serverURL, headers=self.headers, data=payload,
                                auth=(self.rpc_user, self.rpc_pass))
        return response.json()['result']

    def settxfee(self, amount):
        payload = json.dumps({"method": "settxfee", "params": [amount], "jsonrpc": "2.0"})
        response = requests.post(self.serverURL, headers=self.headers, data=payload,
                                auth=(self.rpc_user, self.rpc_pass))
        return response.json()['result']

    # Get Staking info from wallet - getstakinginfo()
    def getstakinginfo(self):
        payload = json.dumps({"method": "getstakinginfo", "params": [], "jsonrpc": "2.0"})
        response = requests.get(self.serverURL, headers=self.headers, data=payload,
                                auth=(self.rpc_user, self.rpc_pass))
        return response.json()['result']

    # Get Staking info from wallet - getstakingstatus()
    def getstakingstatus(self):
        payload = json.dumps({"method": "getstakingstatus", "params": [], "jsonrpc": "2.0"})
        response = requests.post(self.serverURL, headers=self.headers, data=payload,
                                auth=(self.rpc_user, self.rpc_pass))
        return response.json()['result']

    def getreceivedbyaddress(self, params):
        payload = json.dumps({"method": "getreceivedbyaddress", "params": [params], "jsonrpc": "2.0"})
        response = requests.post(self.serverURL, headers=self.headers, data=payload,
                                auth=(self.rpc_user, self.rpc_pass))
        return response.json()['result']

    def getaccount(self, params):
        payload = json.dumps({"method": "getaccount", "params": [params], "jsonrpc": "2.0"})
        response = requests.post(self.serverURL, headers=self.headers, data=payload,
                                auth=(self.rpc_user, self.rpc_pass))
        return response.json()['result'] 

    def getaccountaddress(self, params):
        payload = json.dumps({"method": "getreceivedbyaddress", "params": [params], "jsonrpc": "2.0"})
        response = requests.post(self.serverURL, headers=self.headers, data=payload,
                                auth=(self.rpc_user, self.rpc_pass))
        return response.json()['result']
