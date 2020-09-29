import pymysql.cursors
import warnings
from utils import parsing, output

config = parsing.parse_json('config.json')["mysql"]
host = config["db_host"]
try:
    port = int(config["db_port"])
except KeyError:
    port = 3306
db_user = config["db_user"]
db_pass = config["db_pass"]
db = config["db"]
connection = pymysql.connect(
    host=host,
    port=port,
    user=db_user,
    password=db_pass,
    db=db)
cursor = connection.cursor(pymysql.cursors.DictCursor)

#cursor.execute("DROP DATABASE IF EXISTS {};".format(db))
#cursor.execute("CREATE DATABASE IF NOT EXISTS {};".format(db))
#connection.commit()

cursor.execute("USE {};".format('mysql'))


def run():
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')

        cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            snowflake_pk BIGINT UNSIGNED NOT NULL,
            balance DECIMAL(20, 8) NOT NULL,
            balance_unconfirmed DECIMAL(20, 8) NOT NULL,
            address VARCHAR(34) NOT NULL,
            last_msg_time DATETIME,            
            rain_last_msg_time DATETIME,
            rain_msg_count INT NOT NULL DEFAULT 0,
            PRIMARY KEY (snowflake_pk)
            )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS deposit (
            snowflake_fk BIGINT UNSIGNED NOT NULL,
            amount DECIMAL(20, 8) NOT NULL,
            txid VARCHAR(256) NOT NULL,
            status VARCHAR(20) NOT NULL,
            timestamp DATETIME,
            FOREIGN KEY (snowflake_fk) REFERENCES users(snowflake_pk)
            )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS withdrawal (
            snowflake_fk BIGINT UNSIGNED NOT NULL,
            amount DECIMAL(20, 8) NOT NULL,
            txid VARCHAR(256) NOT NULL,
            status VARCHAR(20) NOT NULL,
            timestamp DATETIME,
            FOREIGN KEY (snowflake_fk) REFERENCES users(snowflake_pk)
            )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS tip (
            snowflake_from_fk BIGINT UNSIGNED NOT NULL,
            snowflake_to_fk BIGINT UNSIGNED NOT NULL,
            amount DECIMAL(20, 8) NOT NULL,
            FOREIGN KEY (snowflake_from_fk) REFERENCES users(snowflake_pk),
            FOREIGN KEY (snowflake_to_fk) REFERENCES users(snowflake_pk)
            )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS server (
            server_id VARCHAR(18) NOT NULL,
            enable_soak TINYINT(1) NOT NULL,
            PRIMARY KEY (server_id)
            )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS channel (
            channel_id VARCHAR(18) NOT NULL,
            server_id VARCHAR(18) NOT NULL,
            enabled TINYINT(1) NOT NULL,
            FOREIGN KEY (server_id) REFERENCES server(server_id),
            PRIMARY KEY (channel_id)
            )""")

if __name__ == '__main__':
    run()