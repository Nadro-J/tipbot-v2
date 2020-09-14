import os
import json
import discord
from datetime import datetime
from discord.ext import commands
from utils import parsing, twitter_auth, rpc_module, cron, mysql_module

rpc = rpc_module.Rpc()
mysql = mysql_module.Mysql()

class Airdrop_commands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        # config(s)
        self.config = parsing.load_json('./configs/airdrop/setup.json')
        self.twitter = parsing.load_json('./configs/airdrop/twitter-config.json')
        self.wallet = parsing.load_json('./configs/airdrop/wallet-config.json')

        # discord channel(s)
        self.channel = self.bot.get_channel(self.config['ann_channel'])

        # interface
        self.color = 0x1e7180
        self.error = 0xcc0000

        self.twitter_auth = twitter_auth.TwitterAuth()
        self.rpc = rpc_module.Rpc()

    roles = parsing.load_json('./configs/airdrop/roles.json')['discord-roles']

    @commands.command()
    @commands.has_any_role(*roles)
    async def getinfo(self, ctx):
        await ctx.message.delete()
        embed = discord.Embed(color=self.color, title=self.config['title'], url=self.config['url'])
        embed.set_thumbnail(url=self.config['thumbnail'])
        embed.set_author(name="Blockchain Information", icon_url=self.config['icon'])
        embed.add_field(name="Chain", value=f"{self.rpc.getinfo()['chain']}", inline=True)
        embed.add_field(name="Blocks", value=f"{self.rpc.getinfo()['blocks']}", inline=True)
        embed.add_field(name="Headers", value=f"{self.rpc.getinfo()['headers']}", inline=True)
        embed.add_field(name="Bestblockhash", value=f"{self.rpc.getinfo()['bestblockhash']}", inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_any_role(*roles)
    async def lasttx(self, ctx):
        await ctx.message.delete()
        lastWalletTransaction = self.rpc.lastWalletTx()
        embed = discord.Embed(color=self.color, title=self.config['title'], url=self.config['url'])
        embed.set_thumbnail(url=self.config['thumbnail'])
        embed.set_author(name="Last transaction", icon_url=self.config['icon'])
        embed.add_field(name=":file_folder: Category", value=f"{lastWalletTransaction['category']}", inline=True)
        embed.add_field(name=":white_check_mark: Confirmations", value=f"{lastWalletTransaction['confirmations']}", inline=True)
        embed.add_field(name=":currency_exchange: Transaction ID", value=f"``{lastWalletTransaction['txid']}``", inline=True)
        embed.add_field(name=":dollar: Amount", value="{0:.8f}".format(lastWalletTransaction['amount']), inline=True)
        if lastWalletTransaction['category'] == 'send':
            embed.add_field(name=":paperclip: Fee", value="{0:.8f}".format(lastWalletTransaction['fee']), inline=True)
        embed.add_field(name=":moneybag: Balance", value="{0:.8f} BITG".format(self.rpc.getbalance()), inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def join(self, ctx, address):
        await ctx.message.delete()
        # temporary storage point(s)
        airdrop_users_TMPLIST = []
        airdrop_addrs_TMPLIST = []
        tmp_twitter = []
        tmp_ids = []
        active_ids = []

        airdropConf = parsing.load_json(self.config['airdrop'])                    # currently joined
        registered_users = parsing.load_json(self.config['twitter'])               # authenticated users
        received = parsing.load_json(self.config['sent'])                          # batch complete users

        if airdropConf['active']:
            airdrop_user_size = airdropConf

            # check if the airdrop is twitter-bounty; if not, limit the amount of users that can join.
            if not airdropConf['twitter-bounty']:
                if (len(airdrop_user_size['airdrop-users'])) >= airdropConf['max-users']:
                    embed = discord.Embed(color=self.color, title=self.config['title'], url=self.config['url'],
                                          description='Unable to join, no slots available.',
                                          timestamp=datetime.utcnow())
                    embed.set_thumbnail(url=self.config['thumbnail'])
                    embed.set_author(name="Better luck next time...",
                                     icon_url=self.config['icon'])
                    await ctx.author.send(embed=embed)
                    return

            if rpc.validateaddress(address)['isvalid']:
                # check if the airdrop is twitter-bounty; if not, limit the amount of users that can join.
                if not airdropConf['twitter-bounty']:
                    if (len(airdrop_user_size['airdrop-users'])) >= airdropConf['max-users']:
                        embed = discord.Embed(color=self.color,
                                              title=self.config['title'],
                                              url=self.config['url'],
                                              description="Unable to join, no slots available.",
                                              timestamp=datetime.utcnow())
                        embed.set_thumbnail(url=self.config['thumbnail'])
                        embed.set_author(name="Better luck next time...",
                                         icon_url=self.config['icon'])
                        await ctx.author.send(embed=embed)
                        return

                # if no one has joined yet, skip. else; add data to tmp arrays to check who has
                # already joined the airdrop.
                if len(airdrop_user_size['airdrop-users']) == 0:
                    pass
                else:
                    for i in range(len(airdropConf['airdrop-users'])):
                        airdrop_users_TMPLIST.append(airdropConf['airdrop-users'][i]['discord-id'])
                        airdrop_addrs_TMPLIST.append(airdropConf['airdrop-users'][i]['address'])

                # When running a twitter-bounty airdrop, check previous participants to avoid double-taking.
                if airdropConf['twitter-bounty']:
                    if len(received['sent']) > 0:
                        for i in range(len(received['sent'])):
                            airdrop_users_TMPLIST.append(received['sent'][i]['discord-id'])

                # store everything in local variables, to be accessed to check if a user has
                # registered already or if the twitter account has already been claimed.
                for i in range(0, len(registered_users['airdrop-users'])):
                    for id in registered_users['airdrop-users'][i].keys():
                        tmp_ids.append(id)
                        tmp_twitter.append(registered_users['airdrop-users'][i][id][0]['twitter'][0]['twitter-id'])

                if parsing.check_duplicate(str(ctx.message.author.id), airdrop_users_TMPLIST) or parsing.check_duplicate(address, airdrop_addrs_TMPLIST):
                    if airdropConf['twitter-bounty']:
                        embed = discord.Embed(color=self.color,
                                              title=self.config['title'], url=self.config['url'],
                                              description="You have already joined the twitter bounty airdrop. If you have not received your coins, be patient. Coins are sent automatically every 6hrs.")
                        embed.set_thumbnail(url=self.config['thumbnail'])
                        embed.set_author(name="Access denied", icon_url=self.config['icon'])
                        await ctx.author.send(embed=embed)
                    else:
                        embed = discord.Embed(color=self.color,
                                              title=self.config['title'], url=self.config['url'],
                                              description="You have already joined the current airdrop.")
                        embed.set_thumbnail(url=self.config['thumbnail'])
                        embed.set_author(name="Access denied", icon_url=self.config['icon'])
                        await ctx.author.send(embed=embed)
                else:
                    if str(ctx.message.author.id) in tmp_ids:
                        # capture more errors.
                        usr_twitter_id = registered_users['airdrop-users'][tmp_ids.index(str(ctx.message.author.id))][str(ctx.message.author.id)][0]['twitter'][0]['twitter-id']
                        if self.twitter_auth.getUserById(usr_twitter_id) == 63:
                            del (registered_users['airdrop-users'][tmp_ids.index(str(ctx.message.author.id))])
                            update_data = json.dumps(registered_users)
                            parsing.dump_json(self.config['twitter'], update_data)

                            embed = discord.Embed(color=self.error,
                                                  title=self.config['title'],
                                                  url=self.config['url'],
                                                  description="Your twitter account has returned True as being suspended. You have been removed as a verified user.")
                            embed.set_thumbnail(url=self.config['thumbnail'])
                            embed.set_author(name="An error has occurred...", icon_url=self.config['icon'])
                            await ctx.author.send(embed=embed)
                        else:

                            if registered_users['airdrop-users'][tmp_ids.index(str(ctx.message.author.id))][str(str(ctx.message.author.id))][0]['verified']:
                                if self.twitter_auth.getFriendship(registered_users['airdrop-users'][tmp_ids.index(str(ctx.message.author.id))][str(str(ctx.message.author.id))][0]['twitter'][0]['twitter-id'], self.twitter['screen-name']):
                                    if airdropConf['twitter-bounty']:
                                        if self.twitter_auth.timeline_retweets(registered_users['airdrop-users'][tmp_ids.index(str(ctx.message.author.id))][str(str(ctx.message.author.id))][0]['twitter'][0]['twitter-id']):

                                            # public airdrop
                                            airdropConf['airdrop-users'].append(({'discord-id': str(ctx.message.author.id), 'address': address}))
                                            update_data = json.dumps(airdropConf)
                                            parsing.dump_json(self.config['airdrop'], update_data) # '<https://twitter.com/%s/status/%s>' % (self.twitter['screen-name'], self.twitter['retweet-id'])
                                            embed = discord.Embed(color=self.color,
                                                                  title=self.config['title'], url=self.config['url'],
                                                                  description=f"<@{ctx.message.author.id}> has joined the bounty airdrop to receive **{airdropConf['amount']}** {self.wallet['ticker']}. Coins are sent in batches (see below for next batch payout).",
                                                                  timestamp=datetime.utcnow())
                                            embed.set_thumbnail(url=self.config['thumbnail'])
                                            embed.set_author(name="Successfully joined!", icon_url=self.config['icon'])
                                            embed.add_field(name="Retweet",
                                                            value=f"<https://twitter.com/{self.twitter['screen-name']}/status/{self.twitter['retweet-id']}>", inline=True)
                                            embed.add_field(name="Next batch payout", value=f"{cron.schedule()}", inline=True)
                                            embed.set_footer(text="An airdrop is taking place, type $join <wallet-address> to participate.")
                                            await self.channel.send(embed=embed)

                                        else:
                                            embed = discord.Embed(color=self.error,
                                                                  title=self.config['title'],
                                                                  url=self.config['url'],
                                                                  description="You must retweet the following link before joining.")
                                            embed.add_field(name='twitter url',
                                                            value=f"https://twitter.com/{self.twitter['screen-name']}/status/{self.twitter['retweet-id']}",
                                                            inline=True)
                                            embed.set_thumbnail(url=self.config['thumbnail'])
                                            embed.set_author(name="One last step...", icon_url=self.config['icon'])
                                            await ctx.author.send(embed=embed)
                                    else:
                                        # non-twitter bounty
                                        airdropConf['airdrop-users'].append(({'discord-id': str(ctx.message.author.id), 'address': address}))
                                        update_data = json.dumps(airdropConf)
                                        parsing.load_json(self.config['airdrop'], update_data)
                                        embed = discord.Embed(color=self.color,
                                                              title=self.config['title'],
                                                              url=self.config['url'],
                                                              description=f"<@{ctx.message.author.id}> has entered the airdrop to receive **{airdropConf['amount']}** {self.wallet['ticker']}, **{airdropConf['max-users'] - len(airdrop_user_size['airdrop-users'])}** slots available.",
                                                              timestamp=datetime.utcnow())
                                        embed.set_thumbnail(url=self.config['thumbnail'])
                                        embed.set_author(name="Successfully joined!", icon_url=self.config['icon'])
                                        embed.set_footer(text="An airdrop is taking place, type $join <wallet-address> to participate.")
                                        await self.channel.send(embed=embed)

                                else:
                                    embed = discord.Embed(color=self.error,
                                                          title=self.config['title'],
                                                          url=self.config['url'],
                                                          description=f"<@{ctx.message.author.id}> You are required to follow <{self.twitter['handle']}>",
                                                          timestamp=datetime.utcnow())
                                    embed.set_thumbnail(url=self.config['thumbnail'])
                                    embed.set_author(name="An error has occurred...", icon_url=self.config['icon'])
                                    await ctx.author.send(embed=embed)
                            else:
                                embed = discord.Embed(color=self.error,
                                                      title=self.config['title'],
                                                      url=self.config['url'],
                                                      description=f"<@{ctx.message.author.id}> You are required to register and verify your twitter account in order to participate.",
                                                      timestamp=datetime.utcnow())
                                embed.set_thumbnail(url=self.config['thumbnail'])
                                await ctx.author.send(embed=embed)

                    else:
                        embed = discord.Embed(color=self.error,
                                              title=self.config['title'],
                                              url=self.config['url'],
                                              description=f"""<@{ctx.message.author.id}>, You are required to register if you wish to participate in current or future airdrops. To register you must follow: <{self.twitter['handle']}>
                                                           \n\nNext verify your Twitter handle by typing:\n ``$register <twitter-handle>``.
                                                           \nIf successful you should receive a unique code via direct message from **disfactor_auth**
                                                            """)
                        embed.add_field(name='Guide',
                                        value="""You will need to adjust your privacy settings to receive the 2FA code.
                                                 **1.** Click on the profile on the top right hand side and click on *"Settings and privacy"*.
                                                 **2.** Next on the left hand pane click *"Privacy and safety"*.
                                                 **3.** You will then see an option under [Direct messages], untick *"Receive Direct Messages from anyone"* and save changed.
                                                 -------------------
                                                 If you do not wish to adjust privacy settings within Twitter then you can follow: <https://twitter.com/disfactor_auth>
                                                 """,
                                        inline=True)
                        embed.set_thumbnail(url=self.config['thumbnail'])
                        embed.set_author(name="How to register", icon_url=self.config['icon'])
                        await ctx.author.send(embed=embed)
            else:
                embed = discord.Embed(color=self.error,
                                      title=self.config['title'],
                                      url=self.config['url'],
                                      description="Please try again.")
                embed.set_thumbnail(url=self.config['thumbnail'])
                embed.set_author(name="Incorrect address", icon_url=self.config['icon'])
                await ctx.author.send(embed=embed)
        else:
            embed = discord.Embed(color=self.error,
                                  title=self.config['title'],
                                  url=self.config['url'],
                                  description="Please try again later.")
            embed.set_thumbnail(url=self.config['thumbnail'])
            embed.set_author(name="No active airdrop", icon_url=self.config['icon'])
            await ctx.author.send(embed=embed)

    @commands.command()
    @commands.has_any_role(*roles)
    async def stats(self, ctx):
        await ctx.message.delete()
        airdropConf = parsing.load_json(self.config['airdrop'])
        users_recvd = parsing.load_json(self.config['sent'])

        embed = discord.Embed(color=self.color)
        embed.set_thumbnail(url=self.config['thumbnail'])
        embed.set_author(name="Airdrop stats", icon_url=self.config['icon'])
        embed.add_field(name="Active", value=f"``{airdropConf['active']}``", inline=True)
        embed.add_field(name="Twitter bounty", value=f"``{airdropConf['twitter-bounty']}``", inline=True)
        embed.add_field(name="Retweet ID", value=f"``{self.twitter['retweet-id']}``", inline=True)
        embed.add_field(name="Users paid", value=f"{len(users_recvd['sent'])}", inline=True)
        embed.add_field(name="Users awaiting payment", value=f"{len(airdropConf['airdrop-users'])}", inline=True)
        embed.add_field(name="Receive", value=f"{airdropConf['amount']} {self.wallet['ticker']} each", inline=True)
        embed.add_field(name="Scheduled payment", value=f"{cron.schedule()}", inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_any_role(*roles)
    async def end(self, ctx, failsafe):
        await ctx.message.delete()
        # If persistent; end differently [check if users are still to be sent in the batch, send anyways regardless of the next batch (if ended).]

        if os.path.isfile(self.config['airdrop']):
            with open(self.config['airdrop']) as file:
                data = json.load(file)

        users_recvd = parsing.load_json(self.config['sent'])
        airdrop_config = parsing.load_json(self.config['airdrop'])
        lastWalletTransaction = self.rpc.lastWalletTx()

        if airdrop_config['active']:
            try:
                failsafe = int(failsafe)
                if failsafe == 1:
                    if airdrop_config['twitter-bounty']:
                        if lastWalletTransaction['confirmations'] >= self.wallet['confirmations']:

                            for user in airdrop_config['airdrop-users']:
                                if len(airdrop_config['airdrop-users']) > 0:
                                    rpc.addParticipant(user['address'], airdrop_config['amount'])

                            # TWITTER_BOUNTY = TRUE
                            # end accordingly...
                            if len(data['airdrop-users']) == 0 and data['twitter-bounty']:
                                cron.disable_batch_airdrop()
                                embed = discord.Embed(color=self.color, timestamp=datetime.utcnow())
                                embed.set_thumbnail(url=self.config['thumbnail'])
                                embed.set_author(name="The twitter bounty airdrop is now over!", icon_url=self.config['icon'])
                                embed.add_field(name="participants", value=f"{len(users_recvd['sent'])}", inline=True)
                                embed.add_field(name="received", value=f"{airdrop_config['amount']} {self.wallet['ticker']} each", inline=True)
                                await self.channel.send(embed=embed)

                                remake_sent = {'sent': []}
                                remake_airdrop = {'airdrop-users': [], 'max-users': 0, 'amount': 0, 'active': False, 'twitter-bounty': False}

                                make_sent = json.dumps(remake_sent, indent=4)
                                make_airdrop = json.dumps(remake_airdrop, indent=4)

                                parsing.dump_json(self.config['sent'], make_sent)
                                parsing.dump_json(self.config['airdrop'], make_airdrop)

                            # TWITTER_BOUNTY = TRUE
                            # send coins to those that have already joined before ending.
                            # auto_recv + airdrop_config['airdrop-users'] = total received
                            else:
                                rpc.sendCoins()
                                rpc.clearRecipients()

                                cron.disable_batch_airdrop()
                                embed = discord.Embed(color=self.color, timestamp=datetime.utcnow())
                                embed.set_thumbnail(url=self.config['thumbnail'])
                                embed.set_author(name="The twitter bounty airdrop is now over!", icon_url=self.config['icon'])
                                embed.add_field(name="participants", value=f"{len(users_recvd['sent']) + len(airdrop_config['airdrop-users'])}", inline=True)
                                embed.add_field(name="received", value=f"{airdrop_config['amount']} {self.wallet['ticker']} each", inline=True)
                                await self.channel.send(embed=embed)

                                remake_sent = {'sent': []}
                                remake_airdrop = {'airdrop-users': [], 'max-users': 0, 'amount': 0, 'active': False, 'twitter-bounty': False}

                                make_sent = json.dumps(remake_sent, indent=4)
                                make_airdrop = json.dumps(remake_airdrop, indent=4)

                                parsing.dump_json(self.config['sent'], make_sent)
                                parsing.dump_json(self.config['airdrop'], make_airdrop)

                        # Not enough transactions
                        elif rpc.lastWalletTx()['confirmations'] < self.wallet['confirmations']:
                            embed = discord.Embed(color=self.error,
                                                  title=self.config['title'],
                                                  url=self.config['url'],
                                                  description="Unable to send, not enough confirmations.",
                                                  timestamp=datetime.utcnow())
                            embed.set_thumbnail(url=self.config['thumbnail'])
                            embed.add_field(name="required", value=f"{self.wallet['confirmations']}", inline=True)
                            embed.add_field(name="confirmations", value=f"{lastWalletTransaction['confirmations']}", inline=True)
                            embed.add_field(name="transaction id", value=f"``{lastWalletTransaction['txid']}``", inline=False)
                            await ctx.send(embed=embed)

                    # TWITTER_BOUNTY = FALSE
                    # end accordingly...
                    if not airdrop_config['twitter-bounty']:
                        remake_airdrop = {'airdrop-users': [], 'max-users': 0, 'amount': 0, 'active': False, 'twitter-bounty': False}
                        make_airdrop = json.dumps(remake_airdrop, indent=4)
                        parsing.dump_json(self.config['airdrop'], make_airdrop)

                        embed = discord.Embed(color=self.color)
                        embed.set_thumbnail(url=self.config['thumbnail'])
                        embed.set_author(name="Airdrop cancelled", icon_url=self.config['icon'])
                        embed.add_field(name="Information", value="The airdrop has been cancelled", inline=True)
                        await self.channel.send(embed=embed)

                elif failsafe != 1:
                    embed = discord.Embed(color=self.error, title=self.config['title'], url=self.config['url'])
                    embed.set_thumbnail(url=self.config['thumbnail'])
                    embed.set_author(name="Unable to cancel airdrop", icon_url=self.config['icon'])
                    embed.add_field(name="Information", value="This command requires a True or False argument. This acts as a failsafe to prevent the accidental cancellation of an airdrops.", inline=False)
                    embed.add_field(name="Command", value="`$end 1`", inline=False)
                    await ctx.send(embed=embed)
            except ValueError:
                embed = discord.Embed(color=self.error)
                embed.set_thumbnail(url=self.config['thumbnail'])
                embed.set_author(name="Unable to cancel airdrop", icon_url=self.config['icon'])
                embed.add_field(name="Information",value="This command requires a True or False argument. This acts as a safety measure to prevent the accidental cancellation of an airdrops.\n\n **Note** - that when a twitter bounty is running that ``$end 1`` is the official way to end the bounty airdrop.", inline=False)
                embed.add_field(name="Command", value="`$end 1`", inline=False)
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(color=self.error, title=self.config['title'], url=self.config['url'])
            embed.set_thumbnail(url=self.config['thumbnail'])
            embed.set_author(name="Unable to cancel airdrop", icon_url=self.config['icon'])
            embed.add_field(name="Information", value="No active airdrop to cancel.", inline=True)
            await ctx.send(embed=embed)

    @commands.command()
    @commands.has_any_role(*roles)
    async def airdrop(self, ctx, participants, cAmount, twitter_bounty: int=0):
        await ctx.message.delete()
        if not parsing.load_json(self.config['airdrop'])['active']:
            try:
                # convert arguments to int, float
                participants = int(participants)
                cAmount = float(cAmount)

                if cAmount > 0:
                    if twitter_bounty:
                        if len(self.twitter['retweet-id']) <= 0:
                            embed = discord.Embed(color=self.error, title=self.config['title'], url=self.config['url'], timestamp=datetime.utcnow())
                            embed.set_thumbnail(url=self.config['thumbnail'])
                            embed.set_author(name="An error has occurred...", icon_url=self.config['icon'])
                            embed.add_field(name="Details", value="You must set a retweet-id before runnning a retweet bounty airdrop.", inline=True)
                            await ctx.send(embed=embed)
                            return

                        cron.enable_batch_airdrop()
                        create_json = {'airdrop-users': [], 'max-users': int(participants), 'amount': float(cAmount), 'active': True, 'twitter-bounty': True}
                        make_json = json.dumps(create_json, indent=4)
                        parsing.dump_json(self.config['airdrop'], make_json)

                        embed = discord.Embed(color=self.color, title=self.config['title'], url=self.config['url'], description='A twitter bounty has been activated! Retweet the URL before joining\n <https://twitter.com/%s/status/%s>' % (self.twitter['screen-name'], self.twitter['retweet-id']))
                        embed.set_thumbnail(url=self.config['thumbnail'])
                        embed.set_author(name="Airdrop in progress", icon_url=self.config['icon'])
                        embed.add_field(name="Information", value="Type ``$join <wallet-address>`` to participate.\n\nUsers that join enter a pool that will automatically payout. During the twitter bounty you can only join/receive once.", inline=False)
                        embed.add_field(name="Next payout", value=f"{cron.schedule()}", inline=True)
                        embed.add_field(name="Amount", value=f"{cAmount} {self.wallet['ticker']} each", inline=True)
                        embed.set_footer(text="Please also check #airdrop-guidance for help registering.")
                        await self.channel.send(embed=embed)
                    else:
                        create_json = {'airdrop-users': [], 'max-users': int(participants),'amount': float(cAmount), 'active': True, 'twitter-bounty': False}
                        make_json = json.dumps(create_json, indent=4)
                        parsing.dump_json(self.config['airdrop'], make_json)

                        embed = discord.Embed(color=self.color,
                                              title=self.config['title'],
                                              url=self.config['url'],
                                              description="An airdrop is taking place, type ``$join <wallet-address>`` to participate.")
                        embed.set_thumbnail(url=self.config['thumbnail'])
                        embed.set_author(name="Airdrop in progress", icon_url=self.config['icon'])
                        embed.add_field(name="Available slots", value=f"{participants}", inline=True)
                        embed.add_field(name="Amount", value=f"{cAmount} {self.wallet['ticker']} each", inline=True)
                        embed.set_footer(text="Please also check #airdrop-guidance for help registering.")
                        await self.channel.send(embed=embed)
                else:
                    embed = discord.Embed(color=self.error, title=self.config['title'], url=self.config['url'], timestamp=datetime.utcnow())
                    embed.set_thumbnail(url=self.config['thumbnail'])
                    embed.set_author(name="An error has occurred...", icon_url=self.config['icon'])
                    embed.add_field(name='Details', value="You must enter a number grater than zero.", inline=True)
                    await self.channel.send(embed=embed)


            except ValueError:
                embed = discord.Embed(color=self.error, title=self.config['title'], url=self.config['url'], timestamp=datetime.utcnow())
                embed.set_thumbnail(url=self.config['thumbnail'])
                embed.set_author(name="An error has occurred...", icon_url=self.config['icon'])
                embed.add_field(name="Details", value="String value given when an integer is expected.", inline=True)
                await self.channel.send(embed=embed)
        else:
            embed = discord.Embed(color=self.error, title=self.config['title'], url=self.config['url'], timestamp=datetime.utcnow())
            embed.set_thumbnail(url=self.config['thumbnail'])
            embed.set_author(name="An error has occurred...", icon_url=self.config['icon'])
            embed.add_field(name="Details", value="An airdrop is currently taking place.", inline=True)
            await self.channel.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 150)
    @commands.has_any_role(*roles)
    async def send(self, ctx):
        await ctx.message.delete()
        if os.path.isfile(self.config['airdrop']):
            with open(self.config['airdrop']) as file:
                data = json.load(file)
                if rpc.lastWalletTx()['confirmations'] >= self.wallet['confirmations']:
                    if data['active'] and len(data['airdrop-users']) > 0 or data['twitter-bounty']:
                        for user in data['airdrop-users']:
                            if len(data['airdrop-users']) == 0:
                                break
                            else:
                                rpc.addParticipant(user['address'], data['amount'])
                        if len(data['airdrop-users']) == 0 and data['twitter-bounty']:
                            return
                        else:
                            total_sent = data['amount'] * len(rpc.recipients)

                            # send transaction
                            rpc.sendmany()
                            rpc.clearRecipients()

                            # Account set to 100000000000000010 for testing, to be changed when in production
                            # Reflect balance on SQL DB
                            mysql.remove_from_balance('100000000000000010', total_sent)
                            mysql.add_withdrawal('100000000000000010', total_sent, rpc.lastWalletTx()['txid'])

                        if data['twitter-bounty']:
                            remake_JSON = {'sent': []}
                            indent_JSON = json.dumps(remake_JSON, indent=4)
                            parsing.dump_json(self.config['sent'], indent_JSON)

                            cron.disable_batch_airdrop()
                            embed = discord.Embed(color=self.color, timestamp=datetime.utcnow())
                            embed.set_thumbnail(url=self.config['thumbnail'])
                            embed.set_author(name="The twitter bounty airdrop is now over!", icon_url=self.config['icon'])
                            embed.add_field(name="participants", value=f"{len(data['airdrop-users'])}", inline=True)
                            embed.add_field(name="received", value=f"{data['amount']} {self.wallet['ticker']} each", inline=True)
                            await self.channel.send(embed=embed)

                        if not data['twitter-bounty']:
                            embed = discord.Embed(color=self.color, timestamp=datetime.utcnow())
                            embed.set_thumbnail(url=self.config['thumbnail'])
                            embed.set_author(name="The airdrop is now complete!", icon_url=self.config['icon'])
                            embed.add_field(name="participants", value=f"{len(data['airdrop-users'])}", inline=True)
                            embed.add_field(name="received", value=f"{data['amount']} {self.wallet['ticker']} each", inline=True)
                            await self.channel.send(embed=embed)

                        remake_airdrop = {'airdrop-users': [], 'max-users': 0, 'amount': 0, 'active': False,'twitter-bounty': False}
                        make_json = json.dumps(remake_airdrop, indent=4)
                        parsing.dump_json(self.config['airdrop'], make_json)

                    elif data['active'] and len(data['airdrop-users']) == 0:
                        embed = discord.Embed(color=self.color,
                                              title=self.config['title'],
                                              url=self.config['url'],
                                              description='Oh no! an error',
                                              timestamp=datetime.utcnow())
                        embed.set_thumbnail(url=self.config['thumbnail'])
                        embed.add_field(name="details", value="Either an airdrop isn't active or not one has joined yet.", inline=True)
                        await self.bot.send_message(ctx.message.channel, embed=embed)

                elif rpc.lastWalletTx()['confirmations'] < self.wallet['confirmations']:
                    embed = discord.Embed(color=self.error,
                                          title=self.config['title'],
                                          url=self.config['url'],
                                          description="Unable to send, not enough confirmations.",
                                          timestamp=datetime.utcnow())
                    embed.set_thumbnail(url=self.config['thumbnail'])
                    embed.add_field(name="required", value=f"{self.wallet['confirmations']}", inline=True)
                    embed.add_field(name="confirmations", value=f"{rpc.lastWalletTx()['confirmations']}", inline=True)
                    embed.add_field(name="transaction id", value=f"``{rpc.lastWalletTx()['txid']}``", inline=False)
                    await self.channel.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 150)
    @commands.has_any_role(*roles)
    async def cmd(self, ctx):
        await ctx.message.delete()
        embed1 = discord.Embed(color=self.color)
        embed2 = discord.Embed(color=self.color)

        embed1.set_thumbnail(url=self.config['thumbnail'])
        embed1.set_author(name="Analytic commands", icon_url=self.config['icon'])
        embed1.add_field(name="command", value="$stats\n$dfa_stats", inline=True)
        embed1.add_field(name="description", value="currently joined\n2FA verified", inline=True)

        embed2.set_thumbnail(url=self.config['thumbnail'])
        embed2.set_author(name="Airdrop commands", icon_url=self.config['icon'])
        embed2.add_field(name="command", value="$getinfo\n$airdrop\n$end\n$getbalance\n$confirm\n$send\n$set_retweet\n$next_payout", inline=True)
        embed2.add_field(name="description", value="general wallet info\nstart airdrop\nend airdrop\nbot balance\nshow confirmations\nsend aidrop\nset retweet status\nshow next payout", inline=True)

        await ctx.send(embed=embed2)
        await ctx.send(embed=embed1)

    @commands.command()
    @commands.has_any_role(*roles)
    async def set_retweet(self,ctx, id: str):
        await ctx.message.delete()
        self.twitter['retweet-id'] = id
        update_config = json.dumps(self.twitter)
        parsing.load_json(self.twitter['self_path'], update_config)

        embed = discord.Embed(color=self.color, title=self.config['title'], url=self.config['url'], timestamp=datetime.utcnow())
        embed.set_thumbnail(url=self.config['thumbnail'])
        embed.set_author(name="Updating retweet-id", icon_url=self.config['icon'])
        embed.add_field(name="complete!", value="retweet-id has now been updated", inline=True)
        await ctx.send(embed=embed)

    ## To be deprecated and replaced with $wallet
    @commands.command()
    @commands.has_any_role(*roles)
    async def getbalance(self, ctx):
        embed = discord.Embed(color=self.color, timestamp=datetime.utcnow())
        embed.set_thumbnail(url=self.config['thumbnail'])
        embed.set_author(name="Wallet balance", icon_url=self.config['icon'])
        embed.add_field(name="Block-Height:", value=rpc_json.getTotalBlocks())
        embed.add_field(name="Balance:", value=f"{rpc_json.getBalance()}", inline=True)
        embed.add_field(name="Address:", value=f"{rpc_json.getAddress()}", inline=False)
        embed.set_image(url=f"https://api.qrserver.com/v1/create-qr-code/?size=100x100&data={rpc_json.getAddress()}")
        await ctx.send(embed=embed)

    # Individual command error handling
    # Note: comment out when troubleshooting command issues
    @airdrop.error
    async def airdrop_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(color=self.error)

            # icon created by: https://www.flaticon.com/authors/icongeek26
            embed.set_thumbnail(url=self.config['thumbnail'])
            embed.set_author(name="Airdrop usage", icon_url=self.config['icon'])
            embed.add_field(name="Arguments", value="`$airdrop {participants} {amount} {twitter-bounty}`", inline=False)
            embed.add_field(name="Normal", value="`$airdrop 25 1 0`", inline=True)
            embed.add_field(name="Twitter bounty", value="`$airdrop 0 1 1`", inline=True)
            await ctx.send(embed=embed)

    @join.error
    async def join_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(color=self.color)
            embed.set_thumbnail(url=self.config['thumbnail'])
            embed.set_author(name="Address not specified", icon_url=self.config['icon'])
            embed.add_field(name="Command", value="`$join GPWb9jprtTkH9Qj5T4xHZiQDkHHh9v8xZa`", inline=True)
            await ctx.author.send(embed=embed)

    @end.error
    async def end_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(color=self.error)
            embed.set_thumbnail(url=self.config['thumbnail'])
            embed.set_author(name="Error! takes 1 argument (0 given)", icon_url=self.config['icon'])
            embed.add_field(name="Information", value="This command requires a True or False argument. This acts as a safety measure to prevent the accidental cancellation of an airdrops.\n\n **Note** - that when a twitter bounty is running that ``$end 1`` is the official way to end the bounty airdrop.", inline=False)
            embed.add_field(name="Command", value="`$end 1`", inline=False)
            await ctx.send(embed=embed)

    @set_retweet.error
    async def set_retweet_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(color=self.error)
            embed.set_thumbnail(url=self.config['thumbnail'])
            embed.set_author(name="Retweet-id not specified", icon_url=self.config['icon'])
            embed.add_field(name="Information", value="Open the retweet on any browser. The URL should display something similar as shown below.\n<https://twitter.com/TwitterAPI/status/1128358947772145672>", inline=False)
            embed.add_field(name="command", value="`$set_retweet 1128358947772145672`", inline=True)
            await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Airdrop_commands(bot))