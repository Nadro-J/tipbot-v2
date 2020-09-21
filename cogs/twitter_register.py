import uuid, json
import discord
from dateutil import parser
from datetime import datetime
from discord.ext import commands

from utils import parsing, twitter_auth, rpc_module

class Twitter_commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # config(s)
        self.config = parsing.load_json('./configs/airdrop/setup.json')
        self.twitter = parsing.load_json('./configs/airdrop/twitter-config.json')

        # interface
        self.color = 0x1e7180
        self.error = 0xcc0000

        self.twitter_auth = twitter_auth.TwitterAuth()

    roles = parsing.load_json('./configs/airdrop/roles.json')['discord-roles']

    @commands.command()
    @commands.has_any_role(*roles)
    async def dfa_stats(self, ctx):
        twitter_data = parsing.load_json(self.config['twitter'])
        verified = 0
        n_verified = 0

        for v in twitter_data['airdrop-users']:
            id = list(v.keys())[0]

            if v[id][0]['verified'] == True:
                verified += 1
            if v[id][0]['verified'] == False:
                n_verified += 1

        embed = discord.Embed(color=self.color, title=self.config['title'], url=self.config['url'])
        embed.set_thumbnail(url=self.config['thumbnail'])
        embed.add_field(name="Total users registered", value=f"{len(twitter_data['airdrop-users'])}", inline=False)
        embed.add_field(name="Verified", value=f"{verified}", inline=True)
        embed.add_field(name="Non-verified", value=f"{n_verified}", inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    async def register_airdrop(self, ctx, handle: str):
        registered_users = parsing.load_json(self.config['twitter'])
        uuid_2fa = uuid.uuid4().hex
        tmp_twitter = []
        tmp_ids = []

        # store everything in local variables, to be accessed to check if a user has
        # registered already or if the twitter account has already been claimed.
        for i in range(0, len(registered_users['airdrop-users'])):
            for id in registered_users['airdrop-users'][i].keys():
                tmp_ids.append(id)
                tmp_twitter.append(registered_users['airdrop-users'][i][id][0]['twitter'][0]['twitter-id'])

        if parsing.check_duplicate(str(ctx.message.author.id), tmp_ids):
            embed = discord.Embed(color=self.error)
            embed.set_thumbnail(url=self.config['thumbnail'])
            embed.set_author(name="You have already registered", icon_url=self.config['icon'])
            embed.add_field(name="Information", value="You can only register one twitter account.", inline=True)
            await ctx.author.send(embed=embed)
        else:
            if self.twitter_auth.getUserByName(handle.lower()) == 50:
                embed = discord.Embed(color=self.error)
                embed.set_thumbnail(url=self.config['thumbnail'])
                embed.set_author(name="No account found", icon_url=self.config['icon'])
                embed.add_field(name="Information", value="Please check that you have the correct Twitter username.",inline=True)
                await ctx.author.send(embed=embed)
            else:
                if parsing.check_duplicate(self.twitter_auth.recipient(handle.lower()), tmp_twitter):
                    embed = discord.Embed(color=self.error)
                    embed.set_thumbnail(url=self.config['thumbnail'])
                    embed.set_author(name="Account already exists", icon_url=self.config['icon'])
                    embed.add_field(name="Information", value="Please check you have the correct Twitter username.", inline=True)
                    await ctx.author.send(embed=embed)
                else:
                    d2fa_message = self.twitter_auth.send_disauth(self.twitter_auth.recipient(handle.lower()), uuid_2fa)
                    if d2fa_message == 349:
                        embed = discord.Embed(color=self.error)
                        embed.set_thumbnail(url=self.config['thumbnail'])
                        embed.set_author(name="Unable to send 2FA code", icon_url=self.config['icon'])
                        embed.add_field(name="Instructions", value="""You will need to adjust your privacy settings to receive the 2FA code.
                                                            **1.** Click on the profile on the top right hand side and click on *"Settings and privacy"*.
                                                            **2.** Next on the left hand pane click *"Privacy and safety"*.
                                                            **3.** You will then see an option under [Direct messages], tick *"Receive Direct Messages from anyone"* and save changed.
                                                            -------------------
                                                            Additionally if you wish to keep your privacy settings how they are you can follow <https://twitter.com/disfactor_auth>
                                                            """, inline=True)
                        await ctx.author.send(embed=embed)

                    else:
                        embed = discord.Embed(color=self.color)
                        embed.set_thumbnail(url=self.config['thumbnail'])
                        embed.set_author(name="Verification sent", icon_url=self.config['icon'])
                        embed.add_field(name="Instructions", value=f"Check your direct messages via Twitter. Once you obtain the verification code, type ``$verify <code>`` to verify that you are the owner of this account. You must also follow {self.twitter['handle']} on Twitter.", inline=True)
                        await ctx.author.send(embed=embed)

                        parsed_dt = parser.parse(self.twitter_auth.getUserByName(handle.lower())['created_at'])

                        registered_users['airdrop-users'].append(({
                                                                  str(ctx.message.author.id):[
                                                                      {
                                                                          'twitter': [
                                                                              {
                                                                                  'twitter-id': self.twitter_auth.recipient(handle.lower()),
                                                                                  'twitter-name': handle.lower(),
                                                                                  'created-on': parsed_dt.strftime('%Y-%m-%d %H:%M:%S')
                                                                              }
                                                                          ],
                                                                          'discord-name': str(ctx.message.author.name),
                                                                          'verified': False,
                                                                          '2fa-code': uuid_2fa,
                                                                          'timestamp': datetime.today().strftime("%Y-%m-%d %H:%M:%S")
                                                                      }
                                                                  ]}))
                        update_json = json.dumps(registered_users)
                        parsing.dump_json(self.config['twitter'], update_json)

    @commands.command()
    async def verify(self, ctx, auth):
        registered_users = parsing.load_json(self.config['twitter'])
        tmp_ids = []

        for i in range(0, len(registered_users['airdrop-users'])):
            for id in registered_users['airdrop-users'][i].keys():
                tmp_ids.append(id)

        if parsing.check_duplicate(str(ctx.message.author.id), tmp_ids):
            disauth_2fa = registered_users['airdrop-users'][tmp_ids.index(str(ctx.message.author.id))][str(str(ctx.message.author.id))][0]['2fa-code']

            if not registered_users['airdrop-users'][tmp_ids.index(str(ctx.message.author.id))][str(str(ctx.message.author.id))][0]['verified']:
                if auth == disauth_2fa:

                    registered_users['airdrop-users'][tmp_ids.index(str(ctx.message.author.id))][str(str(ctx.message.author.id))][0]['verified'] = True

                    update_json = json.dumps(registered_users)
                    parsing.dump_json(self.config['twitter'], update_json)

                    embed = discord.Embed(color=self.color)
                    embed.set_thumbnail(url=self.config['thumbnail'])
                    embed.set_author(name="Registration complete!", icon_url=self.config['icon'])
                    embed.add_field(name="Information", value="You can now participate in future airdrops on Discord.", inline=True)
                    await ctx.author.send(embed=embed)

                else:
                    embed = discord.Embed(color=self.error, title=self.config['title'], url=self.config['url'], description="Invalid 2FA code, please check your twitter direct messages and try again.")
                    embed.set_thumbnail(url=self.config['thumbnail'])
                    await ctx.author.send(embed=embed)

            else:
                embed = discord.Embed(color=self.error, title=self.config['title'], url=self.config['url'], description="You have already verified your account.")
                embed.set_thumbnail(url=self.config['thumbnail'])
                await ctx.author.send(embed=embed)
        else:
            embed = discord.Embed(color=self.color, title=self.config['title'], url=self.config['url'], description='No account found. You need to register before verifying.')
            embed.set_thumbnail(url=self.config['thumbnail'])
            await ctx.author.send(embed=embed)

def setup(bot):
    bot.add_cog(Twitter_commands(bot))