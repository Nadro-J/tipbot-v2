import discord
from discord.ext import commands
from utils import checks, parsing, mysql_module, rpc_module as rpc

mysql = mysql_module.Mysql()
#define bot to use his avatarurl
config = parsing.parse_json('config.json')
bot = commands.Bot(command_prefix=config['prefix'], description=config["description"])

class Wallet(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rpc = rpc.Rpc()

        config        = parsing.parse_json('config.json')
        self.bot_name = config["description"]

        # Coin attributes (BitGreen/BITG)
        self.coin_name       = config["currency_name"]
        self.currency_symbol = config["currency_symbol"]

        # Wallets
        self.treasurer = config["treasurer"]
        self.stake_bal = config["stake_bal"]
        self.donation  = config["donation"]
        self.game_bal  = config["game_bal"]
        self.airdrop   = config["airdrop"]

        # Parse the embed section of the config file
        embed_config     = parsing.parse_json('config.json')["embed_msg"]
        self.thumb_embed = embed_config["thumb_embed_url"]
        self.footer_text = embed_config["footer_msg_text"]
        self.embed_color = int(embed_config["color"], 16)

    @commands.command(hidden=True)
    @commands.check(checks.is_owner)
    async def wallet(self, ctx):
        """Show wallet info [ADMIN ONLY]"""
        #rpc commands for getinfo
        info = self.rpc.getinfo()

        #below used for active user calculation
        rain_config = parsing.parse_json('config.json')['rain']
        RAIN_REQUIRED_USER_ACTIVITY_M = rain_config['user_activity_required_m']
        active_id_users = mysql.get_active_users_id(RAIN_REQUIRED_USER_ACTIVITY_M, True)

        if ctx.message.guild is not None:
            await ctx.message.delete()

        #embed starts here
        embed=discord.Embed(title="\u200b", color=self.embed_color, inline=False)
        embed.set_author(name="{}".format(self.bot_name))
        embed.set_thumbnail(url="http://{}".format(self.thumb_embed))

        embed.add_field(name="__:bank: Wallet__",
                        value="**RPC Balance**"
                              "\n> {0}\n"
                              "**Connections**"
                              "\n> {1}\n"
                              "**Block-Height**"
                              "\n> {2}\n".format(self.rpc.getbalance(),
                                               self.rpc.getconnectioncount(),
                                               info["blocks"]), inline=True)
        embed.add_field(name="__:man_farmer::man_farmer: Stats__",
                        value="**Registered users**"
                              "\n> {0}\n"
                              "**Active users**"
                              "\n> {1}".format(len(mysql.get_reg_users_id()),
                                                 len(active_id_users)), inline=True)
        embed.add_field(name="__:cloud_rain: Rain settings__",
                        value="**Minimum rain**"
                              "\n> {0:.8f}\n"
                              "**Maximum recipients**"
                              "\n> {1}".format(rain_config['min_amount'],
                                                 rain_config['max_recipients']), inline=True)

        embed.add_field(name="\u200b\n", value="\u200b\n", inline=False)

        # Wallet information
        embed.add_field(name="__:bank: Treasurer__",
                        value="``{0}``\n"
                              "**Balance**: {1:.6f}\n\u200b".format(mysql.get_address(self.treasurer),
                                                 mysql.get_balance(self.treasurer, check_update=True)), inline=True)
        embed.add_field(name="__:cut_of_meat: Staking__",
                        value="``{0}``\n"
                              "**Balance**: {1:.6f}\n\u200b".format(mysql.get_address(self.stake_bal),
                                                 mysql.get_balance(self.stake_bal, check_update=True)), inline=True)

        embed.add_field(name="\u200b\n", value="\u200b\n", inline=True)  # Buffer

        embed.add_field(name="__:dollar: Donation__",
                        value="``{0}``\n"
                              "**Balance**: {1:.6f}\n\u200b".format(mysql.get_address(self.donation),
                                                 mysql.get_balance(self.donation, check_update=True)), inline=True)
        embed.add_field(name="__:game_die: Game__",
                        value="``{0}``\n"
                              "**Balance**: {1:.6f}\n\u200b".format(mysql.get_address(self.game_bal),
                                                 mysql.get_balance(self.game_bal, check_update=True)), inline=True)
        embed.add_field(name=":airplane: Airdrop",
                        value="`{0}`\n"
                              "**Balance:** {1:.6f}".format(mysql.get_address(self.airdrop),
                                                 mysql.get_balance(self.airdrop, check_update=True)), inline=True)

        embed.add_field(name="\u200b\n", value="\u200b\n", inline=True)  # Buffer

        embed.set_footer(text=self.footer_text)
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            await self.bot.say("I need the `Embed links` permission to send this")

    @commands.command(hidden=True)
    @commands.check(checks.is_owner)
    async def banserver(self, ctx, server: int):
        """Ban a server from using the bot [ADMIN ONLY]"""
        soak_status = mysql.check_for_server_status(server)

        if ctx.message.guild is not None:
            await ctx.message.delete()

        if soak_status is None:
            await ctx.send("Server ID: {} is not registered with this bot. The server will now be registered and marked as banned".format(server))
            mysql.check_server(server)
            mysql.ban_server(server, 2)
            await ctx.send("Server ID: {} is now registered with this bot and BANNED.".format(server))
        elif soak_status == 2:
            await ctx.send("Server ID: {} is already BANNED.".format(server))
        else:
            mysql.ban_server(server, 2)
            await ctx.send("Server ID: {} is now marked as BANNED.".format(server))

    @commands.command(hidden=True)
    @commands.check(checks.is_owner)
    async def unbanserver(self, ctx, server: int):
        """Un-Ban a server that is currently marked as BANNED [ADMIN ONLY]"""

        soak_status = mysql.check_for_server_status(server)

        if ctx.message.guild is not None:
            await ctx.message.delete()

        if soak_status is None:
            await ctx.send("Server ID: {} is not registered with this bot. This server cannot be UNBANNED.".format(server))
        elif soak_status == 1:
            await ctx.send("Server ID: {} is already UNBANNED.".format(server))
        else:
            mysql.ban_server(server, 1)
            await ctx.send("Server ID: {} is now marked as UNBANNED.".format(server))

def setup(bot):
    bot.add_cog(Wallet(bot))

