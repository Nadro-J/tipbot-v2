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
        if ctx.message.guild is not None:
            await ctx.message.delete()

        embed = discord.Embed(color=self.color, title=self.config['title'], url=self.config['url'])
        embed.set_thumbnail(url=self.config['thumbnail'])
        embed.set_author(name="Blockchain Information", icon_url=self.config['icon'])
        embed.add_field(name=":chains: Chain", value=f"{self.rpc.getinfo()['chain']}", inline=True)
        embed.add_field(name=":green_square: Blocks", value=f"{self.rpc.getinfo()['blocks']}", inline=True)
        embed.add_field(name=":green_square: Headers", value=f"{self.rpc.getinfo()['headers']}", inline=True)
        embed.add_field(name=":hash: Bestblockhash", value=f"`{self.rpc.getinfo()['bestblockhash']}`", inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_any_role(*roles)
    async def lasttx(self, ctx):
        lastWalletTransaction = self.rpc.lastWalletTx()

        if ctx.message.guild is not None:
            await ctx.message.delete()

        embed = discord.Embed(color=self.color, title=self.config['title'], url=self.config['url'])
        embed.set_thumbnail(url=self.config['thumbnail'])
        embed.set_author(name="Last transaction", icon_url=self.config['icon'])
        embed.add_field(name=":file_folder: Category", value=f"{lastWalletTransaction['category']}", inline=True)
        embed.add_field(name=":white_check_mark: Confirmations", value=f"{lastWalletTransaction['confirmations']}", inline=True)
        embed.add_field(name=":currency_exchange: Previous TX ID", value=f"``{lastWalletTransaction['txid']}``", inline=True)
        embed.add_field(name=":dollar: Amount", value="{0:.8f}".format(lastWalletTransaction['amount']), inline=True)
        if lastWalletTransaction['category'] == 'send':
            embed.add_field(name=":paperclip: Fee", value="{0:.8f}".format(lastWalletTransaction['fee']), inline=True)
        embed.add_field(name=":moneybag: Balance", value="{0:.8f} BITG".format(self.rpc.getbalance()), inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def join(self, ctx, address):
        # temporary storage point(s)
        airdrop_users_TMPLIST = []
        airdrop_addrs_TMPLIST = []
        tmp_twitter = []
        tmp_ids = []
        active_ids = []

        airdropConf = parsing.load_json(self.config['airdrop'])                    # currently joined
        registered_users = parsing.load_json(self.config['twitter'])               # authenticated users
        received = parsing.load_json(self.config['sent'])                          # batch complete users

        if ctx.message.guild is not None:
            await ctx.message.delete()

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
                                            embed.add_field(name=":bird: Retweet",
                                                            value=f"<https://twitter.com/{self.twitter['screen-name']}/status/{self.twitter['retweet-id']}>", inline=True)
                                            embed.add_field(name=":alarm_clock: Next batch payout", value=f"{cron.schedule()}", inline=True)
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
                                        parsing.dump_json(self.config['airdrop'], update_data)
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
        airdropConf = parsing.load_json(self.config['airdrop'])
        alreadySent = parsing.load_json(self.config['sent'])

        if ctx.message.guild is not None:
            await ctx.message.delete()

        embed = discord.Embed(color=self.color)
        embed.set_thumbnail(url=self.config['thumbnail'])
        embed.set_author(name="Airdrop stats", icon_url=self.config['icon'])
        embed.add_field(name="Active", value=f"``{airdropConf['active']}``", inline=True)
        embed.add_field(name="Twitter bounty", value=f"``{airdropConf['twitter-bounty']}``", inline=True)
        embed.add_field(name=":bird: Retweet ID", value=f"``{self.twitter['retweet-id']}``", inline=True)
        embed.add_field(name=":man_farmer: Users paid", value=f"{len(alreadySent['sent'])}", inline=True)
        embed.add_field(name=":man_farmer: Users awaiting payment", value=f"{len(airdropConf['airdrop-users'])}", inline=True)
        embed.add_field(name=":moneybag: Receive", value=f"{airdropConf['amount']} {self.wallet['ticker']} each", inline=True)
        embed.add_field(name=":calendar_spiral: Scheduled payment", value=f"{cron.schedule()}", inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_any_role(*roles)
    async def end(self, ctx, failsafe):
        # If persistent; end differently [check if users are still to be sent in the batch, send anyways regardless of the next batch (if ended).]

        if os.path.isfile(self.config['airdrop']):
            with open(self.config['airdrop']) as file:
                data = json.load(file)

        alreadySent = parsing.load_json(self.config['sent'])
        airdropConf = parsing.load_json(self.config['airdrop'])
        lastWalletTransaction = self.rpc.lastWalletTx()

        if ctx.message.guild is not None:
            await ctx.message.delete()

        if airdropConf['active']:
            try:
                failsafe = int(failsafe)
                if failsafe == 1:
                    if airdropConf['twitter-bounty']:
                        if lastWalletTransaction['confirmations'] >= self.wallet['confirmations']:
                            for user in airdropConf['airdrop-users']:
                                if len(airdropConf['airdrop-users']) > 0:
                                    rpc.addParticipant(user['address'], airdropConf['amount'])

                            # TWITTER_BOUNTY = TRUE
                            # end accordingly...
                            if len(data['airdrop-users']) == 0 and data['twitter-bounty']:
                                cron.disable_batch_airdrop()
                                embed = discord.Embed(color=self.color, timestamp=datetime.utcnow())
                                embed.set_thumbnail(url=self.config['thumbnail'])
                                embed.set_author(name="The twitter bounty airdrop is now over!", icon_url=self.config['icon'])
                                embed.add_field(name=":man_farmer::man_farmer: Participants", value=f"{len(alreadySent['sent'])}", inline=True)
                                embed.add_field(name="Received", value=f"{airdropConf['amount']} {self.wallet['ticker']} each", inline=True)
                                await self.channel.send(embed=embed)

                                remake_sent = {'sent': []}
                                remake_airdrop = {'airdrop-users': [], 'max-users': 0, 'amount': 0, 'active': False, 'twitter-bounty': False}

                                make_sent = json.dumps(remake_sent, indent=4)
                                make_airdrop = json.dumps(remake_airdrop, indent=4)

                                parsing.dump_json(self.config['sent'], make_sent)
                                parsing.dump_json(self.config['airdrop'], make_airdrop)

                            # TWITTER_BOUNTY = TRUE
                            # send coins to those that have already joined before ending.
                            # auto_recv + airdropConf['airdrop-users'] = total received
                            else:
                                # send transactions
                                rpc.sendmany()
                                rpc.clearRecipients()

                                total_sent = airdropConf['amount'] * len(rpc.recipients)

                                # Account set to 100000000000000010 for testing, to be changed when in production
                                # Reflect balance on SQL DB
                                mysql.remove_from_balance('100000000000000014', total_sent)
                                mysql.add_withdrawal('100000000000000014', total_sent, rpc.lastWalletTx()['txid'])

                                cron.disable_batch_airdrop()
                                embed = discord.Embed(color=self.color, timestamp=datetime.utcnow())
                                embed.set_thumbnail(url=self.config['thumbnail'])
                                embed.set_author(name="The twitter bounty airdrop is now over!", icon_url=self.config['icon'])
                                embed.add_field(name=":man_farmer::woman_farmer: participants", value=f"{len(alreadySent['sent']) + len(airdropConf['airdrop-users'])}", inline=True)
                                embed.add_field(name=":moneybag: Received", value=f"{airdropConf['amount']} {self.wallet['ticker']} each", inline=True)
                                await self.channel.send(embed=embed)

                                remake_sent = {'sent': []}
                                remake_airdrop = {'airdrop-users': [], 'max-users': 0, 'amount': 0, 'active': False, 'twitter-bounty': False}

                                make_sent = json.dumps(remake_sent, indent=4)
                                make_airdrop = json.dumps(remake_airdrop, indent=4)

                                parsing.dump_json(self.config['sent'], make_sent)
                                parsing.dump_json(self.config['airdrop'], make_airdrop)

                        # Not enough transactions
                        elif rpc.lastWalletTx()['confirmations'] < self.wallet['confirmations']:
                            if len(airdropConf['airdrop-users']) != 0:
                                embed = discord.Embed(color=self.error,
                                                      title=self.config['title'],
                                                      url=self.config['url'],
                                                      description="Unable to send, not enough confirmations.",
                                                      timestamp=datetime.utcnow())
                                embed.set_thumbnail(url=self.config['thumbnail'])
                                embed.add_field(name=":exclamation: Required", value=f"{self.wallet['confirmations']}", inline=True)
                                embed.add_field(name=":white_check_mark: Confirmations", value=f"{lastWalletTransaction['confirmations']}", inline=True)
                                embed.add_field(name=":currency_exchange: Previous TX ID", value=f"``{lastWalletTransaction['txid']}``", inline=False)
                                await ctx.send(embed=embed)
                            else:
                                cron.disable_batch_airdrop()
                                embed = discord.Embed(color=self.color, timestamp=datetime.utcnow())
                                embed.set_thumbnail(url=self.config['thumbnail'])
                                embed.set_author(name="The twitter bounty airdrop is now over!", icon_url=self.config['icon'])
                                embed.add_field(name=":man_farmer::woman_farmer: participants", value=f"{len(alreadySent['sent']) + len(airdropConf['airdrop-users'])}", inline=True)
                                embed.add_field(name=":moneybag: Received", value=f"{airdropConf['amount']} {self.wallet['ticker']} each", inline=True)
                                await self.channel.send(embed=embed)

                                remake_sent = {'sent': []}
                                remake_airdrop = {'airdrop-users': [], 'max-users': 0, 'amount': 0, 'active': False, 'twitter-bounty': False}

                                make_sent = json.dumps(remake_sent, indent=4)
                                make_airdrop = json.dumps(remake_airdrop, indent=4)

                                parsing.dump_json(self.config['sent'], make_sent)
                                parsing.dump_json(self.config['airdrop'], make_airdrop)


                    # TWITTER_BOUNTY = FALSE
                    # end accordingly...
                    if not airdropConf['twitter-bounty']:
                        remake_airdrop = {'airdrop-users': [], 'max-users': 0, 'amount': 0, 'active': False, 'twitter-bounty': False}
                        make_airdrop = json.dumps(remake_airdrop, indent=4)
                        parsing.dump_json(self.config['airdrop'], make_airdrop)

                        embed = discord.Embed(color=self.color)
                        embed.set_thumbnail(url=self.config['thumbnail'])
                        embed.set_author(name="Airdrop cancelled", icon_url=self.config['icon'])
                        embed.add_field(name=":information_source: Information", value="The airdrop has been cancelled", inline=True)
                        await self.channel.send(embed=embed)

                elif failsafe != 1:
                    embed = discord.Embed(color=self.error, title=self.config['title'], url=self.config['url'])
                    embed.set_thumbnail(url=self.config['thumbnail'])
                    embed.set_author(name="Unable to cancel airdrop", icon_url=self.config['icon'])
                    embed.add_field(name=":information_source: Information", value="This command requires a True or False argument. This acts as a failsafe to prevent the accidental cancellation of an airdrops.", inline=False)
                    embed.add_field(name=":keyboard: Command", value="`$end 1`", inline=False)
                    await ctx.send(embed=embed)
            except ValueError:
                embed = discord.Embed(color=self.error)
                embed.set_thumbnail(url=self.config['thumbnail'])
                embed.set_author(name="Unable to cancel airdrop", icon_url=self.config['icon'])
                embed.add_field(name=":information_source: Information",value="This command requires a True or False argument. This acts as a safety measure to prevent the accidental cancellation of an airdrops.\n\n **Note** - that when a twitter bounty is running that ``$end 1`` is the official way to end the bounty airdrop.", inline=False)
                embed.add_field(name=":keyboard: Command", value="`$end 1`", inline=False)
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(color=self.error, title=self.config['title'], url=self.config['url'])
            embed.set_thumbnail(url=self.config['thumbnail'])
            embed.set_author(name="Unable to cancel airdrop", icon_url=self.config['icon'])
            embed.add_field(name=":information_source: Information", value="No active airdrop to cancel.", inline=True)
            await ctx.send(embed=embed)

    @commands.command()
    @commands.has_any_role(*roles)
    async def airdrop(self, ctx, participants, cAmount, twitter_bounty: int=0):
        if ctx.message.guild is not None:
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

                        embed = discord.Embed(color=self.color, title=self.config['title'], url=self.config['url'], description=f"{ctx.message.guild.default_role} - A twitter bounty has been activated! Retweet the URL before joining\n <https://twitter.com/{self.twitter['screen-name']}/status/{self.twitter['retweet-id']}>")
                        embed.set_thumbnail(url=self.config['thumbnail'])
                        embed.set_author(name=":airplane::droplet: Airdrop in progress", icon_url=self.config['icon'])
                        embed.add_field(name=":information_source: Information", value="Type ``$join <wallet-address>`` to participate.\n\nUsers that join enter a pool that will automatically payout. During the twitter bounty you can only join/receive once.", inline=False)
                        embed.add_field(name=":alarm_clock: Next payout", value=f"{cron.schedule()}", inline=True)
                        embed.add_field(name=":moneybag: Amount", value=f"{cAmount} {self.wallet['ticker']} each", inline=True)
                        embed.set_footer(text="Please also check #airdrop-guidance for help registering.")
                        await self.channel.send(embed=embed)
                    else:
                        create_json = {'airdrop-users': [], 'max-users': int(participants),'amount': float(cAmount), 'active': True, 'twitter-bounty': False}
                        make_json = json.dumps(create_json, indent=4)
                        parsing.dump_json(self.config['airdrop'], make_json)

                        embed = discord.Embed(color=self.color,
                                              title=self.config['title'],
                                              url=self.config['url'],
                                              description=f"{ctx.message.guild.default_role} - An airdrop is taking place, type ``$join <wallet-address>`` to participate.")
                        embed.set_thumbnail(url=self.config['thumbnail'])
                        embed.set_author(name=":airplane::droplet: Airdrop in progress", icon_url=self.config['icon'])
                        embed.add_field(name=":person_raising_hand: Available slots", value=f"{participants}", inline=True)
                        embed.add_field(name=":moneybag: Amount", value=f"{cAmount} {self.wallet['ticker']} each", inline=True)
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
                            balance = mysql.get_balance('100000000000000014', check_update=True)

                            if float(balance) < total_sent:
                                await ctx.send("{} **:warning: Airdrop wallet is empty! :warning:**".format(ctx.message.author.mention))
                                return

                            # send transaction
                            rpc.sendmany()
                            rpc.clearRecipients()

                            mysql.remove_from_balance('100000000000000014', total_sent)

                        if data['twitter-bounty']:
                            remake_JSON = {'sent': []}
                            indent_JSON = json.dumps(remake_JSON, indent=4)
                            parsing.dump_json(self.config['sent'], indent_JSON)

                            cron.disable_batch_airdrop()
                            embed = discord.Embed(color=self.color, timestamp=datetime.utcnow())
                            embed.set_thumbnail(url=self.config['thumbnail'])
                            embed.set_author(name="The twitter bounty airdrop is now over! :bird:", icon_url=self.config['icon'])
                            embed.add_field(name=":man_farmer::man_farmer: Participants", value=f"{len(data['airdrop-users'])}", inline=True)
                            embed.add_field(name=":moneybag: Received", value=f"{data['amount']} {self.wallet['ticker']} each", inline=True)
                            await self.channel.send(embed=embed)

                        if not data['twitter-bounty']:
                            embed = discord.Embed(color=self.color, timestamp=datetime.utcnow())
                            embed.set_thumbnail(url=self.config['thumbnail'])
                            embed.set_author(name="The airdrop is now complete!", icon_url=self.config['icon'])
                            embed.add_field(name=":man_farmer::man_farmer: Participants", value=f"{len(data['airdrop-users'])}", inline=True)
                            embed.add_field(name=":moneybag: received", value=f"{data['amount']} {self.wallet['ticker']} each", inline=True)
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
                    embed.add_field(name=":exclamation: Required", value=f"{self.wallet['confirmations']}", inline=True)
                    embed.add_field(name=":white_check_mark: Confirmations", value=f"{rpc.lastWalletTx()['confirmations']}", inline=True)
                    embed.add_field(name=":currency_exchange: Previous TX ID", value=f"``{rpc.lastWalletTx()['txid']}``", inline=False)
                    await self.channel.send(embed=embed)

    @commands.command()
    @commands.has_any_role(*roles)
    async def admin(self, ctx):
        await ctx.message.delete()
        embed1 = discord.Embed(color=self.color)
        embed2 = discord.Embed(color=self.color)

        embed1.set_thumbnail(url=self.config['thumbnail'])
        embed1.set_author(name="Analytic commands", icon_url=self.config['icon'])
        embed1.add_field(name="Command", value="$stats\n$dfa_stats", inline=True)
        embed1.add_field(name="Description", value="currently joined\n2FA verified", inline=True)

        embed2.set_thumbnail(url=self.config['thumbnail'])
        embed2.set_author(name="Airdrop commands", icon_url=self.config['icon'])
        embed2.add_field(name="Command", value="$getinfo\n$airdrop\n$end\n$getbalance\n$confirm\n$send\n$set_retweet\n$next_payout", inline=True)
        embed2.add_field(name="Description", value="general wallet info\nstart airdrop\nend airdrop\nbot balance\nshow confirmations\nsend aidrop\nset retweet status\nshow next payout", inline=True)

        await ctx.send(embed=embed2)
        await ctx.send(embed=embed1)

    @commands.command()
    @commands.has_any_role(*roles)
    async def set_retweet(self,ctx, id: str):
        await ctx.message.delete()
        self.twitter['retweet-id'] = id
        update_config = json.dumps(self.twitter)
        parsing.dump_json(self.twitter['self_path'], update_config)
        embed = discord.Embed(color=self.color, title=self.config['title'], url=self.config['url'], timestamp=datetime.utcnow())
        embed.set_thumbnail(url=self.config['thumbnail'])
        embed.set_author(name="Updating retweet-id", icon_url=self.config['icon'])
        embed.add_field(name="complete!", value="retweet-id has now been updated", inline=True)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Airdrop_commands(bot))