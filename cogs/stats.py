import discord, os
from discord.ext import commands
from utils import checks, parsing, output
from aiohttp import ClientSession
import urllib.request
import json

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_config = parsing.parse_json('config.json')["embed_msg"]
        self.thumb_embed = self.embed_config["thumb_embed_url"]

    @commands.command()
    async def coingecko(self, ctx):
        """
        Show stats about BitGreen
        """
        if ctx.message.guild is not None:
            await ctx.message.delete()

        headers={"user-agent" : "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.78 Safari/537.36"}

        async with ClientSession() as session:
            async with session.get("https://api.coingecko.com/api/v3/coins/bitcoin-green", headers=headers) as response:
                responseRaw = await response.read()
                responseRaw = json.loads(responseRaw)

                # price change percentage
                _24H = responseRaw['market_data']['price_change_percentage_24h']
                _7D  = responseRaw['market_data']['price_change_percentage_7d']
                _14D = responseRaw['market_data']['price_change_percentage_14d']

                embed = discord.Embed(color=0x00FF00)
                embed.set_author(name=' BitGreen Market Information', icon_url="http://{}".format(self.embed_config["thumb_embed_url"]))
                embed.add_field(name=":dollar: __Price__",
                                value="**USD:** {0:.8f} \n"
                                      "**BTC:** {1:.8f} \n"
                                      "**GBP:** {2:.8f} \n"
                                      "**EUR:** {3:.8f}".format(responseRaw['market_data']['current_price']['usd'],
                                                                responseRaw['market_data']['current_price']['btc'],
                                                                responseRaw['market_data']['current_price']['gbp'],
                                                                responseRaw['market_data']['current_price']['eur']),
                                inline=True)

                embed.add_field(name=":bar_chart:  __24H Volume__",
                                value="**USD:** {0:,} \n"
                                      "**BTC:** {1:,} \n"
                                      "**GBP:** {2:,} \n"
                                      "**EUR:** {3:,}".format(responseRaw['market_data']['total_volume']['usd'],
                                                              responseRaw['market_data']['total_volume']['btc'],
                                                              responseRaw['market_data']['total_volume']['gbp'],
                                                              responseRaw['market_data']['total_volume']['eur']), inline=True)

                embed.add_field(name=":information_source:  __Supply__",
                                    value="**Max Supply:** {0:,} \n"
                                          "**Circulating Supply:** {1:,} \n"
                                          "**Coins left to mine:** {2:,} \n".format(responseRaw['market_data']['total_supply'],
                                                                                    responseRaw['market_data']['circulating_supply'],
                                                                                    responseRaw['market_data']['total_supply'] - responseRaw['market_data']['circulating_supply']),
                                inline=True)

                embed.add_field(name=":chart_with_downwards_trend: __Change__",
                                value=f"**24H:** {_24H}% {':small_red_triangle_down:' if _24H < 0 else ''}\n"
                                      f"**7D:** {_7D}% {':small_red_triangle_down:' if _7D < 0 else ''}\n"
                                      f"**14D:** {_14D}% {':small_red_triangle_down:' if _14D < 0 else ''}\n", inline=True)

                embed.add_field(name=":chart_with_upwards_trend: __24H High / Low__",
                                value="**High:** {0:.8f} BTC\n**Low:** {1:.8f} BTC".format(responseRaw['market_data']['high_24h']['btc'], responseRaw['market_data']['low_24h']['btc']),
                                inline=True)

                embed.add_field(name=":lizard:   __CoinGecko__",
                                value="**Market cap rank:** {0} \n"
                                      "**CoinGecko Score:** {1:.8f} \n"
                                      "**liquidity Score:** {2:.8f} \n"
                                      "**Community Score:** {3:.8f}".format(responseRaw['market_cap_rank'],
                                                                            responseRaw['coingecko_score'],
                                                                            responseRaw['liquidity_score'],
                                                                            responseRaw['community_score']), inline=True)
                await ctx.send(embed=embed)



def setup(bot):
    bot.add_cog(Stats(bot))
