from utils import parsing, mysql_module

config = parsing.parse_json('config.json')

mysql = mysql_module.Mysql()


def is_owner(ctx):
    return ctx.message.author.id in config["owners"]

def is_server_owner(ctx):
    return ctx.message.author.id == ctx.message.server.owner

def in_server(ctx):
    return ctx.message.server is not None

def is_online(ctx):
    return True
    
def allow_soak(ctx):
    return mysql.check_soak(ctx.message.server)
