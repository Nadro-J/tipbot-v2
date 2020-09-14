from discord.ext import commands


class Invite(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def invite(self, ctx):
        """
        Get the bot's invite link
        """
        if ctx.message.guild is not None:
            await ctx.message.delete()

        await ctx.send(":tada: https://discordapp.com/oauth2/authorize?permissions=0&client_id={}&scope=bot".format(self.bot.user.id))

def setup(bot):
    bot.add_cog(Invite(bot))
