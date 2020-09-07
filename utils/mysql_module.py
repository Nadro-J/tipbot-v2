import pymysql.cursors
import discord
from utils import parsing, rpc_module, helpers
from decimal import Decimal
import datetime

rpc = rpc_module.Rpc()

MIN_CONFIRMATIONS_FOR_DEPOSIT = 2


class Mysql:
    """
    Singleton helper for complex database methods
    """
    instance = None

    def __init__(self):
        if not Mysql.instance:
            Mysql.instance = Mysql.__Mysql()

    def __getattr__(self, name):
        return getattr(self.instance, name)

    class __Mysql:
        def __init__(self):
            config = parsing.parse_json('config.json')["mysql"]
            self.__host = config["db_host"]
            self.__port = int(config.get("db_port", 3306))
            self.__db_user = config["db_user"]
            self.__db_pass = config["db_pass"]
            self.__db = config["db"]
            self.__connected = 1
            self.__setup_connection()
            self.txfee = parsing.parse_json('config.json')["txfee"]
            self.stakeflake = parsing.parse_json('config.json')["stake_bal"]

        def __setup_connection(self):
            self.__connection = pymysql.connect(
                host=self.__host,
                port=self.__port,
                user=self.__db_user,
                password=self.__db_pass,
                db=self.__db)

        def __setup_cursor(self, cur_type):
            # ping the server and reset the connection if it is down
            self.__connection.ping(True)
            return self.__connection.cursor(cur_type)

# region User
        def make_user(self, snowflake, address):
            cursor = self.__setup_cursor(
                pymysql.cursors.DictCursor)
            to_exec = "INSERT INTO users (snowflake_pk, balance, balance_unconfirmed, address) VALUES(%s, %s, %s, %s)"
            cursor.execute(
                to_exec, (str(snowflake), '0', '0', str(address)))
            cursor.close()
            self.__connection.commit()

        def check_for_user(self, snowflake):
            """
            Checks for a new user (NO LONGER CREATES A NEW USER - THAT IS HANDLED BY bot.py)
            """
            cursor = self.__setup_cursor(
                pymysql.cursors.DictCursor)
            to_exec = "SELECT snowflake_pk, address, balance, balance_unconfirmed, last_msg_time, rain_last_msg_time, rain_msg_count FROM users WHERE snowflake_pk LIKE %s"
            cursor.execute(to_exec, (str(snowflake)))
            result_set = cursor.fetchone()
            cursor.close()
            return result_set

        def check_for_user_and_make(self, snowflake):
            """
            Checks for a new user and creates one if not in DB
            """
            cursor = self.__setup_cursor(
                pymysql.cursors.DictCursor)
            to_exec = "SELECT snowflake_pk, address, balance, balance_unconfirmed, last_msg_time, rain_last_msg_time, rain_msg_count FROM users WHERE snowflake_pk LIKE %s"
            cursor.execute(to_exec, (str(snowflake)))
            result_set = cursor.fetchone()
            cursor.close()

            if result_set is None:
                address = rpc.getnewaddress(snowflake)
                self.make_user(snowflake, address)
            
            return result_set

        def register_user(self, snowflake):
            """
            Registers a new user
            """
            cursor = self.__setup_cursor(
                pymysql.cursors.DictCursor)
            to_exec = "SELECT snowflake_pk, address, balance, balance_unconfirmed, last_msg_time, rain_last_msg_time, rain_msg_count FROM users WHERE snowflake_pk LIKE %s"
            cursor.execute(to_exec, (str(snowflake)))
            result_set = cursor.fetchone()
            cursor.close()

            if result_set is None:
                address = rpc.getnewaddress(str(snowflake))
                self.make_user(snowflake, address)
                
        def get_user(self, snowflake):
            cursor = self.__setup_cursor(
                pymysql.cursors.DictCursor)
            to_exec = "SELECT snowflake_pk, balance, balance_unconfirmed, address, last_msg_time, rain_last_msg_time, rain_msg_count FROM users WHERE snowflake_pk LIKE %s"
            cursor.execute(to_exec, (str(snowflake)))
            result_set = cursor.fetchone()
            cursor.close()
            return result_set

        #get staking user
        def get_staking_user(self, snowflake):
            if snowflake == self.stakeflake:
                cursor = self.__setup_cursor(
                    pymysql.cursors.DictCursor)
                to_exec = "SELECT snowflake_pk, balance, balance_unconfirmed FROM users WHERE snowflake_pk LIKE %s"
                cursor.execute(to_exec, (str(snowflake)))
                result_set = cursor.fetchone()
                cursor.close()
                return result_set
            else:
                return None

        #get user balance
        def get_user_balance(self, snowflake):
            cursor = self.__setup_cursor(
                pymysql.cursors.DictCursor)
            to_exec = "SELECT snowflake_pk, balance, balance_unconfirmed FROM users WHERE snowflake_pk LIKE %s"
            cursor.execute(to_exec, (str(snowflake)))
            result_set = cursor.fetchone()
            cursor.close()
            return result_set           

        def get_user_by_address(self, address):
            cursor = self.__setup_cursor(
                pymysql.cursors.DictCursor)           
            to_exec = "SELECT snowflake_pk, balance, balance_unconfirmed, address, last_msg_time, rain_last_msg_time, rain_msg_count FROM users WHERE address LIKE %s"
            cursor.execute(to_exec, (str(address)))
            result_set = cursor.fetchone()
            cursor.close()
            return result_set

        def get_address(self, snowflake):
            result_set = self.get_user(snowflake)
            return result_set.get("address")
# endregion

# region Servers/Channels
        def check_server(self, server: discord.Guild):
            if server is None:
                return
            cursor = self.__setup_cursor(
                pymysql.cursors.DictCursor)        
            to_exec = "SELECT server_id, enable_soak FROM server WHERE server_id LIKE %s"
            cursor.execute(to_exec, (server.id))
            result_set = cursor.fetchone()
            cursor.close()

            if result_set is None:
                self.add_server(server)

        def add_server(self, server: discord.Guild):
            cursor = self.__setup_cursor(
                pymysql.cursors.DictCursor)
            to_exec = "INSERT INTO server (server_id, enable_soak) VALUES(%s, %s)"
            cursor.execute(
                # if the discord server is considered large - more than 250 user - the default soak is set to true or 1
                to_exec, (str(server.id), str(int(server.large))))
            cursor.close()
            self.__connection.commit()

        def add_ban_server(self, server: int):
            ban_call = 2
            cursor = self.__setup_cursor(
                pymysql.cursors.DictCursor)
            to_exec = "INSERT INTO server (server_id, enable_soak) VALUES(%s, %s)"
            cursor.execute(
                to_exec, (str(server), str(ban_call)))
            cursor.close()
            self.__connection.commit()

        def ban_server(self, server: int, ban_status):
            cursor = self.__setup_cursor(
                pymysql.cursors.DictCursor)
            # enable_soak value 2 will equal the server is banned
            to_exec = "UPDATE server SET enable_soak = %s WHERE server_id = %s"
            cursor.execute(
                to_exec, (str(ban_status), str(server)))
            cursor.close()
            self.__connection.commit()

        # check only if the server exist - does not add the server if it does not
        def check_for_server_status(self, server):
            if server is None:
                return False
            cursor = self.__setup_cursor(
                pymysql.cursors.DictCursor)
            to_exec = "SELECT enable_soak FROM server WHERE server_id = %s"
            cursor.execute(to_exec, (str(server)))
            result_set = cursor.fetchone()
            cursor.close()
            return result_set

        def remove_server(self, server: discord.Guild):
            cursor = self.__setup_cursor(
                pymysql.cursors.DictCursor)
            to_exec = "DELETE FROM server WHERE server_id = %s"
            cursor.execute(to_exec, (str(server.id),))
            to_exec = "DELETE FROM channel WHERE server_id = %s"
            cursor.execute(to_exec, (str(server.id),))
            cursor.close()
            self.__connection.commit()

        def add_channel(self, channel):
            cursor = self.__setup_cursor(
                pymysql.cursors.DictCursor)            
            to_exec = "INSERT INTO channel(channel_id, server_id, enabled) VALUES(%s, %s, 1)"
            cursor.execute(
                to_exec, (str(channel.id), str(channel.server.id)))
            cursor.close()
            self.__connection.commit()

        def remove_channel(self, channel):
            cursor = self.__setup_cursor(
                pymysql.cursors.DictCursor)            
            to_exec = "DELETE FROM channel WHERE channel_id = %s"
            cursor.execute(to_exec, (str(channel.id),))
            cursor.close()
            self.__connection.commit()
# endregion

# region Balance
        def set_balance(self, snowflake, to, is_unconfirmed = False):
            cursor = self.__setup_cursor(
                pymysql.cursors.DictCursor)
            if is_unconfirmed:
                to_exec = "UPDATE users SET balance_unconfirmed = %s WHERE snowflake_pk = %s"
            else:
                to_exec = "UPDATE users SET balance = %s WHERE snowflake_pk = %s"
            cursor.execute(to_exec, (to, snowflake,))
            cursor.close()
            self.__connection.commit()

        def get_balance(self, snowflake, check_update=False, check_unconfirmed = False):
            #run check to see if staking user
            if str(snowflake) == self.stakeflake:
                if check_update:
                    self.check_for_updated_mining_balance()
                result_set = self.get_staking_user(snowflake)
                if check_unconfirmed:
                    return result_set.get("balance_unconfirmed")
                else:
                    return result_set.get("balance")
            else:
                if check_update:
                    self.check_for_updated_balance(snowflake)

                result_set = self.get_user(snowflake)
                if check_unconfirmed:
                    return result_set.get("balance_unconfirmed")
                else:
                    return result_set.get("balance")

        def add_to_balance(self, snowflake, amount, is_unconfirmed = False):
            self.set_balance(snowflake, self.get_balance(
                snowflake) + Decimal(amount))

        def remove_from_balance(self, snowflake, amount):
            self.set_balance(snowflake, self.get_balance(
                snowflake) - Decimal(amount))

        def add_to_balance_unconfirmed(self, snowflake, amount):
            balance_unconfirmed = self.get_balance(snowflake, check_unconfirmed = True) 
            self.set_balance(snowflake, balance_unconfirmed + Decimal(amount), is_unconfirmed = True)

        def remove_from_balance_unconfirmed(self, snowflake, amount):
            balance_unconfirmed = self.get_balance(snowflake, check_unconfirmed = True) 
            self.set_balance(snowflake, balance_unconfirmed - Decimal(amount), is_unconfirmed = True)
            
        def check_for_updated_balance(self, snowflake):
            """
            Uses RPC to get the latest transactions and updates
            the user balances accordingly

            This code is based off of parse_incoming_transactions in
            https://github.com/tehranifar/ZTipBot/blob/master/src/wallet.py
            """
            transaction_list = rpc.listtransactions(snowflake, 100)
            for tx in transaction_list:
                if tx["category"] != "receive":
                    continue
                if tx.get('generated') is True:
                    continue
                txid = tx["txid"]
                amount = tx["amount"]
                confirmations = tx["confirmations"]
                address = tx["address"]
                status = self.get_transaction_status_by_txid(txid)
                user = self.get_user_by_address(address)

                # This address isn't a part of any user's account
                if not user:
                    continue

                snowflake_cur = user["snowflake_pk"]
                if status == "DOESNT_EXIST" and confirmations >= MIN_CONFIRMATIONS_FOR_DEPOSIT:
                    self.add_to_balance(snowflake_cur, amount)
                    self.add_deposit(snowflake_cur, amount, txid, 'CONFIRMED')
                elif status == "DOESNT_EXIST" and confirmations < MIN_CONFIRMATIONS_FOR_DEPOSIT:
                    self.add_deposit(snowflake_cur, amount,
                                     txid, 'UNCONFIRMED')
                    self.add_to_balance_unconfirmed(snowflake_cur, amount)
                elif status == "UNCONFIRMED" and confirmations >= MIN_CONFIRMATIONS_FOR_DEPOSIT:
                    self.add_to_balance(snowflake_cur, amount)
                    self.remove_from_balance_unconfirmed(snowflake_cur, amount)
                    self.confirm_deposit(txid)

        #staking check
        def check_for_updated_mining_balance(self):
            """
            Uses RPC to get the latest transactions and updates
            the user balances accordingly

            This code is based off of parse_incoming_transactions in
            https://github.com/tehranifar/ZTipBot/blob/master/src/wallet.py
            """
            #snowflake of staking account
            snowflake = str(self.stakeflake)
            #create a new user for staking stake
            #generate snowflake
            #self.check_for_user_and_make(snowflake)
            user = self.get_staking_user(snowflake)
            
            all_users = [x for x in self.get_reg_users_id() if x is not snowflake]

            for ids in all_users:
                if str(ids) == snowflake:
                    continue

                # first you must get the transactions of the account holder
                transaction_list = rpc.listtransactions(str(ids), 100)

                for tx in transaction_list:
                    # if the generated tag is true this is a stake        
                    if tx.get('generated') is None:
                        # a stake will not affect the individual users balance
                        continue

                    txid = tx["txid"]
                    amount = 0.5
                    confirmations = int(tx["confirmations"])
                    mint_status = tx["generated"]
                    status = self.get_transaction_status_by_txid(txid)

                    #acreddit the staking user throughout the confirmation process
                    #the stake will take longer to confirm
                    snowflake_cur = snowflake
                    if status == "DOESNT_EXIST" and mint_status is True:
                        self.add_to_balance(snowflake_cur, amount)
                        self.add_deposit(snowflake_cur, amount, txid, 'CONFIRMED-STAKE')
                    elif status == "DOESNT_EXIST" and confirmations < 101:
                        self.add_deposit(snowflake_cur, amount,
                                        txid, 'UNCONFIRMED-STAKE')
                        self.add_to_balance_unconfirmed(snowflake_cur, amount)
                    elif status == "UNCONFIRMED-STAKE" and confirmations >= 101:
                        self.add_to_balance(snowflake_cur, amount)
                        self.remove_from_balance_unconfirmed(snowflake_cur, amount)
                        self.confirm_stake(txid)

                    #once confirmed split the stake between users balance %
                

        def get_transaction_status_by_txid(self, txid):
            cursor = self.__setup_cursor(
                pymysql.cursors.DictCursor)
            to_exec = "SELECT status FROM deposit WHERE txid = %s"
            cursor.execute(to_exec, (txid,))
            result_set = cursor.fetchone()
            cursor.close()
            if not result_set:
                return "DOESNT_EXIST"

            return result_set["status"]
# endregion

# region Deposit/Withdraw/Tip/Soak
        def add_deposit(self, snowflake, amount, txid, status):
            cursor = self.__setup_cursor(
                pymysql.cursors.DictCursor)
            to_exec = "INSERT INTO deposit(snowflake_fk, amount, txid, status) VALUES(%s, %s, %s, %s)"
            cursor.execute(
                to_exec, (str(snowflake), str(amount), str(txid), str(status)))
            cursor.close()
            self.__connection.commit()

        def confirm_deposit(self, txid):
            cursor = self.__setup_cursor(
                pymysql.cursors.DictCursor)
            to_exec = "UPDATE deposit SET status = %s WHERE txid = %s"
            cursor.execute(to_exec, ('CONFIRMED', str(txid)))
            cursor.close()
            self.__connection.commit()


        #confirm the stake with the status=CONRIRMED-STAKE
        def confirm_stake(self, txid):
            cursor = self.__setup_cursor(
                pymysql.cursors.DictCursor)
            to_exec = "UPDATE deposit SET status = %s WHERE txid = %s"
            cursor.execute(to_exec, ('CONFIRMED-STAKE', str(txid)))
            cursor.close()
            self.__connection.commit()

        def create_withdrawal(self, snowflake, address, amount):
            res = rpc.settxfee(self.txfee)
            if not res:
                return None

            txid = rpc.sendtoaddress(address, amount - self.txfee)
            if not txid:
                return None

            self.remove_from_balance(snowflake, amount)
            return self.add_withdrawal(snowflake, amount, txid)

        def add_withdrawal(self, snowflake, amount, txid):
            cursor = self.__setup_cursor(
                pymysql.cursors.DictCursor)
            to_exec = "INSERT INTO withdrawal(snowflake_fk, amount, txid) VALUES(%s, %s, %s)"
            cursor.execute(
                to_exec, (str(snowflake), str(amount), str(txid)))
            cursor.close()
            self.__connection.commit()
            return txid

        def add_tip(self, snowflake_from_fk, snowflake_to_fk, amount):
            self.remove_from_balance(snowflake_from_fk, amount)
            self.add_to_balance(snowflake_to_fk, amount)
            cursor = self.__setup_cursor(
                pymysql.cursors.DictCursor)
            tip_exec = "INSERT INTO tip(snowflake_from_fk, snowflake_to_fk, amount) VALUES(%s, %s, %s)"
            cursor.execute(
                tip_exec, (str(snowflake_from_fk), str(snowflake_to_fk), str(amount)))
            cursor.close()
            self.__connection.commit()

        def check_soak(self, server: discord.Guild) -> bool:
            if server is None:
                return False
            self.check_server(server)
            cursor = self.__setup_cursor(
                pymysql.cursors.DictCursor)
            to_exec = "SELECT enable_soak FROM server WHERE server_id = %s"
            cursor.execute(to_exec, (str(server.id)))
            result_set = cursor.fetchone()
            cursor.close()
            return result_set['enable_soak']

        def set_soak(self, server, to):
            self.check_server(server)
            cursor = self.__setup_cursor(
                pymysql.cursors.DictCursor)
            to_exec = "UPDATE server SET enable_soak = %s WHERE server_id = %s"
            cursor.execute(to_exec, (to, str(server.id),))
            cursor.close()
            self.__connection.commit()
# endregion

# region Last message
        def user_last_msg_check(self, user_id, content, is_private):
            #if the user is not registered 
            if self.get_user(user_id) is None:
                return False
            else:
                user = self.check_for_user(user_id)
                # if using is missing return false
                if user is None:
                    return False

                # Get difference in seconds between now and last msg. If it is less than 1s, return False
                if user["last_msg_time"] is not None:
                    since_last_msg_s = (datetime.datetime.utcnow() - user["last_msg_time"]).total_seconds()
                    if since_last_msg_s < 1:
                        return False
                else:
                    since_last_msg_s = None

                # Do not process the messages made in DM
                if not is_private:
                    self.update_last_msg(user, since_last_msg_s, content)

                return True

        def update_last_msg(self, user, last_msg_time, content):
            rain_config = parsing.parse_json('config.json')['rain']
            min_num_words_required = rain_config["min_num_words_required"]
            delay_between_messages_required_s = rain_config["delay_between_messages_required_s"]            
            user_activity_required_m = rain_config["user_activity_required_m"]

            content_adjusted = helpers.unicode_strip(content)
            words = content_adjusted.split(' ')
            adjusted_count = 0
            prev_len = 0
            for word in words:
                word = word.strip()
                cur_len = len(word)
                if cur_len > 0:
                    if word.startswith(":") and word.endswith(":"):
                        continue
                    if prev_len == 0:
                        prev_len = cur_len
                        adjusted_count += 1
                    else:
                        res = prev_len % cur_len
                        prev_len = cur_len
                        if res != 0:
                            adjusted_count += 1
                if adjusted_count >= min_num_words_required:
                    break

            if last_msg_time is None:
                user["rain_msg_count"] = 0
            else:                
                if last_msg_time >= (user_activity_required_m * 60):
                    user["rain_msg_count"] = 0
            
            is_accepted_delay_between_messages = False
            if user["rain_last_msg_time"] is None:
                is_accepted_delay_between_messages = True
            elif (datetime.datetime.utcnow() - user["rain_last_msg_time"]).total_seconds() > delay_between_messages_required_s:
                is_accepted_delay_between_messages = True

            if adjusted_count >= min_num_words_required and is_accepted_delay_between_messages:
                user["rain_msg_count"] += 1
                user["rain_last_msg_time"] = datetime.datetime.utcnow()
            user["last_msg_time"]=datetime.datetime.utcnow()

            cursor = self.__setup_cursor(
                pymysql.cursors.DictCursor)
            to_exec = "UPDATE users SET last_msg_time = %s, rain_last_msg_time = %s, rain_msg_count = %s WHERE snowflake_pk = %s"
            cursor.execute(to_exec, (user["last_msg_time"], user["rain_last_msg_time"], user["rain_msg_count"], user["snowflake_pk"]))

            cursor.close()
            self.__connection.commit()                      
# endregion

# region Active users

        def get_active_users_id(self, user_activity_since_minutes, is_rain_activity):         
            since_ts = datetime.datetime.utcnow() - datetime.timedelta(minutes=user_activity_since_minutes)
        
            cursor = self.__setup_cursor(
                pymysql.cursors.DictCursor)
            if not is_rain_activity:
                to_exec = "SELECT snowflake_pk, balance, balance_unconfirmed, address, last_msg_time, rain_last_msg_time, rain_msg_count FROM users WHERE last_msg_time > %s ORDER BY snowflake_pk"
            else:
                to_exec = "SELECT snowflake_pk, balance, balance_unconfirmed, address, last_msg_time, rain_last_msg_time, rain_msg_count FROM users WHERE rain_last_msg_time > %s ORDER BY snowflake_pk"
            cursor.execute(to_exec, (str(since_ts)))
            users = cursor.fetchall()
            cursor.close()
            
            return_ids = []
            for user in users:
                return_ids.append(user["snowflake_pk"])
                
            return return_ids

# endregion

# region Registered users

        def get_reg_users_id(self):         
            cursor = self.__setup_cursor(
                pymysql.cursors.DictCursor)
            to_exec = "SELECT snowflake_pk FROM users ORDER BY snowflake_pk"
            cursor.execute(to_exec)
            users = cursor.fetchall()
            cursor.close()
            
            return_reg_ids = []
            for user in users:
                return_reg_ids.append(user["snowflake_pk"])
                
            return return_reg_ids
# endregion

# transaction history related calls - deposits

        #return a list of txids of a users deposit transactions
        def get_deposit_list(self, status):
            #database search
            cursor = self.__setup_cursor(
                pymysql.cursors.DictCursor)
            to_exec = "SELECT amount, txid FROM deposit WHERE status = %s"
            cursor.execute(to_exec, str(status))
            deposits = cursor.fetchall()
            cursor.close()

            return_deptxid_list = []
            for transaction in deposits:
                return_deptxid_list.append(transaction["txid"])

            return return_deptxid_list

        #return a list of txids of a users deposit transactions
        def get_deposit_list_byuser(self, snowflake):
            #database search
            cursor = self.__setup_cursor(
                pymysql.cursors.DictCursor)
            to_exec = "SELECT snowflake_fk, amount, txid FROM deposit WHERE snowflake_fk = %s"
            cursor.execute(to_exec, str(snowflake))
            deposits = cursor.fetchall()
            cursor.close()

            return_deptxid_list = []
            for transaction in deposits:
                return_deptxid_list.append(transaction["txid"])

            return return_deptxid_list

        #get deposit info from txid
        def get_deposit_amount(self, txid):
            cursor = self.__setup_cursor(
                pymysql.cursors.DictCursor)
            to_exec = "SELECT snowflake_fk, amount, txid, status FROM deposit WHERE txid = %s"
            cursor.execute(to_exec, str(txid))
            deposit = cursor.fetchone()
            cursor.close()

            return deposit["amount"]

# endregion

# transaction history related calls - withdrawals

        #return a list of txids of a users withdrawal transactions
        def get_withdrawal_list_byuser(self, snowflake):
            #database search
            cursor = self.__setup_cursor(
                pymysql.cursors.DictCursor)
            to_exec = "SELECT snowflake_fk, amount, txid FROM withdrawal WHERE snowflake_fk = %s"
            cursor.execute(to_exec, str(snowflake))
            deposits = cursor.fetchall()
            cursor.close()

            return_wittxid_list = []
            for transaction in deposits:
                return_wittxid_list.append(transaction["txid"])

            return return_wittxid_list

        #get deposit info from txid
        def get_withdrawal_amount(self, txid):
            cursor = self.__setup_cursor(
                pymysql.cursors.DictCursor)
            to_exec = "SELECT snowflake_fk, amount, txid FROM withdrawal WHERE txid = %s"
            cursor.execute(to_exec, str(txid))
            withdrawal = cursor.fetchone()
            cursor.close()

            return withdrawal["amount"]

# endregion

# tip information calls
        def get_tip_amounts_from_id(self, snowflake, snowflake_to):
            cursor = self.__setup_cursor(
                pymysql.cursors.DictCursor)
            to_exec = "SELECT snowflake_to_fk, amount FROM tip WHERE snowflake_from_fk = %s"
            cursor.execute(to_exec, str(snowflake))
            user_tips = cursor.fetchall()
            cursor.close()
            
            return_tip_amounts = []
            for tips in user_tips:
                if int(tips["snowflake_to_fk"]) == int(snowflake_to):
                    return_tip_amounts.append(tips["amount"])
                
            return return_tip_amounts

# end region