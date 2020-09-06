import discord, datetime, time
from discord.ext import commands
from utils import parsing, checks

start_time = time.time()

class Uptime(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        config = parsing.parse_json('config.json')
        self.coin_name = config["currency_name"]
        self.bot_name = config["description"]

        #parse the embed section of the config file
        embed_config = parsing.parse_json('config.json')["embed_msg"]
        self.thumb_embed = embed_config["thumb_embed_url"]
        self.footer_text = embed_config["footer_msg_text"]
        self.embed_color = int(embed_config["color"], 16)


    @commands.command()
    @commands.check(checks.is_owner)
    async def uptime(self, ctx):
        """
        Get the time the bot has been active [ADMIN ONLY]
        """
        current_time = time.time()
        difference = int(round(current_time - start_time))
        text = str(datetime.timedelta(seconds=difference))
        embed=discord.Embed(title="You requested **Tip Bot Uptime**", color=self.embed_color)
        embed.set_author(name="{}".format(self.bot_name))
        embed.set_thumbnail(url="http://{}".format(self.thumb_embed))
        embed.add_field(name="Uptime", value=text)
        embed.set_footer(text=self.footer_text)
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            await ctx.send("Current uptime: " + text)


def setup(bot):
    bot.add_cog(Uptime(bot))
