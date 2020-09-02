import discord, os
from discord.ext import commands
from utils import checks, output

class Pull(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True, hidden=True)
    @commands.check(checks.is_owner)
    async def pull(self, ctx):
        """
        Update the bot [ADMIN ONLY]
        """
        await self.bot.say("Pulling...")
        try:
            returned = os.system("git pull")
            await self.bot.say(":+1:Returned code "+ str(returned))
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            output.error('{} has attempted to update the bot, but the following '
                         'exception occurred;\n\t->{}'.format(ctx.message.author, exc))


def setup(bot):
    bot.add_cog(Pull(bot))
