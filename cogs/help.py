import discord
from discord.ext import commands
from utils import checks, parsing

class Help(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot = bot        
        bot.remove_command('help')
        config = parsing.parse_json('config.json')        
        self.prefix = config["prefix"]
        self.bot_descr = config["description"]
        self.color = 0x1e7180
        self.error = 0xcc0000

    @commands.command()
    async def help(self, ctx):
        """
        Displays a useful list of commands.
        """
        if ctx.message.guild is not None:
            await ctx.message.delete()

        try:
            embed = discord.Embed(color=self.color, title='Command list')
            embed.set_thumbnail(url=self.bot.user.avatar_url)
            embed.set_author(name=self.bot_descr, icon_url=self.bot.user.avatar_url)
            embed.add_field(name=":bank: Wallet Commands", value="$deposit\n$withdraw\n$dlist\n$wlist\n$balance\n$tip", inline=True)
            embed.add_field(name=":money_with_wings: Distribute", value=f"$soak\n$rain", inline=True)
            embed.add_field(name=":game_die: Game", value=f"$bet", inline=True)
            await ctx.send(embed=embed)
            if ctx.message.guild is not None:
                await ctx.message.delete()
                await ctx.send("{}, I PMed you some helpful info! Make sure to double check that it is from me!".format(ctx.message.author.mention))
        except discord.HTTPException:
            await ctx.send("I need the `Embed links` permission to send this")

def setup(bot):
    bot.add_cog(Help(bot))