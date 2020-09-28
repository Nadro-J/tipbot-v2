#!/usr/bin/env python3
import os, json
from datetime import datetime
from utils import rpc_module, mysql_module, parsing

rpc = rpc_module.Rpc()
mysql = mysql_module.Mysql()

class task():
    def __init__(self):
        self.relative_path  = os.path.dirname(os.path.abspath(__file__))
        self.config         = parsing.load_json(f'{self.relative_path}/configs/airdrop/setup.json')
        self.sent           = parsing.load_json(f'{self.relative_path}/configs/airdrop/persistent-sent.json')
        self.airdropConf    = parsing.load_json(f'{self.relative_path}/configs/airdrop/current-airdrop.json')
        self.wallet         = parsing.load_json(f'{self.relative_path}/configs/airdrop/wallet-config.json')
        self.batch_log      = f'{self.relative_path}/logs/batch-log.txt'

    # debugging; log time each batch task has been completed
    def task_logging(self):
        batch_log = open(self.batch_log, 'a')
        batch_log.write(f'[{datetime.now()}] - Batch airdrop complete!\n')

    def batch_airdrop(self):
            if self.airdropConf['active'] and self.airdropConf['twitter-bounty']:
                if len(self.airdropConf['airdrop-users']) == 0:
                    print (f"{parsing.timestamp()} - No recipients")
                    return

                for user in self.airdropConf['airdrop-users']:
                    self.sent['sent'].append(user)

                # "[1:]" added to remove . <- period from filepath
                update_sent = json.dumps(self.sent)
                parsing.dump_json(self.relative_path + self.config['sent'][1:], update_sent)

                if rpc.lastWalletTx()['confirmations'] >= self.wallet['confirmations']:
                    for user in self.airdropConf['airdrop-users']:
                        if len(self.airdropConf['airdrop-users']) == 0:
                            break
                        else:
                            rpc.addParticipant(user['address'], self.airdropConf['amount'])

                    total_sent = self.airdropConf['amount'] * len(rpc.recipients)
                    balance = mysql.get_balance('100000000000000014', check_update=True)

                    if float(balance) < total_sent:
                        print(f"{parsing.timestamp()} - Airdrop wallet is empty!")
                        return

                    # send transactions
                    print (f"{parsing.timestamp()} - Sending {total_sent} coins to {len(rpc.recipients)} addresses")
                    rpc.sendmany()
                    rpc.clearRecipients()

                    mysql.remove_from_balance('100000000000000014', total_sent)

                    # change 'current-airdrop.json' by moving participants to 'persistent-sent.json'
                    self.airdropConf['airdrop-users'] = []
                    update_airdropConf = json.dumps(self.airdropConf)
                    parsing.dump_json(self.relative_path + self.config['airdrop'][1:], update_airdropConf)
                    self.task_logging()
                else:
                    print (f"{parsing.timestamp()} - Not enough .")
            else:
                print (f"{parsing.timestamp()} - Twitter bounty isn't running.")

task().batch_airdrop()