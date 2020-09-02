import discord, os
from discord.ext import commands
from utils import checks, output
from aiohttp import ClientSession
import urllib.request
import json

class Stats(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot = bot

    @commands.command()
    async def stats(self, amount=1):
        """
        Show stats about HTMLCOIN
        """
        headers={"user-agent" : "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.78 Safari/537.36"}
        try:
            async with ClientSession() as session:
                async with session.get("https://api.coingecko.com/api/v3/coins/htmlcoin", headers=headers) as response:
                    responseRaw = await response.read()
                    priceData = json.loads(responseRaw)
                    for item in priceData:
                        embed = discord.Embed(color=0x00FF00)
                        embed.set_author(name='HTMLCOIN Coin Information', icon_url="i.ibb.co/GkBSpV3/logo-icon-no-txt-32x32.png")
                        embed.add_field(name="current_price", value="${}".format(item['usd']))
                        #embed.add_field(name="Price (BTC)", value="{} BTC".format(item['btc']))
                        #embed.add_field(name='\Altmarkets',value='\altmarkets')
                        #embed.add_field(name="Volume (USD)", value="${}".format(item['24h_volume_usd']))
                        #embed.add_field(name="Market Cap", value="${}".format(item['market_cap_usd']))
                        #embed.add_field(name='\u200b',value='\u200b')
                        #embed.add_field(name="% 1h", value="{}%".format(item['percent_change_1h']))
                        #embed.add_field(name="% 24h", value="{}%".format(item['percent_change_24h']))
                        #embed.add_field(name="% 7d", value="{}%".format(item['percent_change_7d']))
                        #embed.add_field(name="Circulating Supply", value="{} HTMLCOIN".format(item['available_supply']))
                        #embed.add_field(name="Total Supply", value="{} HTMLCOIN".format(item['total_supply']))
                        embed.set_footer(text="https://www.coingecko.com/en/coins/htmlcoin", icon_url="i.ibb.co/GkBSpV3/logo-icon-no-txt-32x32.png")
                    await self.bot.say(embed=embed)
        except:
            await self.bot.say(":warning: Error fetching prices!")


def setup(bot):
    bot.add_cog(Stats(bot))
