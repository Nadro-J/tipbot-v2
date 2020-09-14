from discord.ext import commands
from utils import parsing, cron

class cronJob_commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = parsing.load_json('./config/setup.json')
        self.twitter = parsing.load_json('./config/twitter-config.json')

    roles = parsing.load_json('./configs/airdrop/roles.json')['discord-roles']

    @commands.command()
    @commands.has_any_role(*roles)
    async def setup_batch_cron(self, ctx):
        cron.create_cronjob()
        await ctx.message.delete()
        await ctx.send(":white_check_mark: cronjob created!")

    @commands.command()
    @commands.has_any_role(*roles)
    async def enable_batch_airdrop(self, ctx):
        cron.enable_batch_airdrop()
        await ctx.message.delete()
        await ctx.send(":white_check_mark: cronjob enabled!")

    @commands.command()
    @commands.has_any_role(*roles)
    async def disable_batch_airdrop(self, ctx):
        cron.disable_batch_airdrop()
        await ctx.message.delete()
        await ctx.send(":warning: cronjob disabled!")

def setup(bot):
    bot.add_cog(cronJob_commands(bot))