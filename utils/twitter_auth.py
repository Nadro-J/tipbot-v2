import sys
import tweepy
from utils import parsing
thrdPartyAuthConfig = parsing.load_json('./configs/airdrop/authenticate.json')

class TwitterAuth():
    def __init__(self):
        self.auth = tweepy.OAuthHandler(thrdPartyAuthConfig['twitter-api_k'], thrdPartyAuthConfig['twitter-secret_k'])
        self.auth.set_access_token(thrdPartyAuthConfig['twitter-access'], thrdPartyAuthConfig['twitter-token'])
        self.api = tweepy.API(self.auth, wait_on_rate_limit=True, parser=tweepy.parsers.JSONParser())

    ##########################################################
    ## GET FUNCTIONS #########################################
    # get details by twitter id: 00112233445566
    def getUserById(self, id):
        try:
            return self.api.get_user(id=id)
        except tweepy.TweepError as error:
            return error.api_code

    # get details by username: @n4dro
    def getUserByName(self, name):
        try:
            return self.api.get_user(screen_name=name)
        except tweepy.TweepError as error:
            return error.api_code

    # get user timeline
    def getTimelineById(self, id):
        try:
            return self.api.user_timeline(id=id)
        except tweepy.TweepError as error:
            return error.api_code

    # check if the user is following the set account
    def getFriendship(self, source, target):
        try:
            return self.api.show_friendship(source_id=source, target_screen_name=target)['relationship']['source']['following']
        except tweepy.TweepError as error:
            return error.api_code

    # scrape user timeline for retweets
    def timeline_retweets(self, id):
        retweets = []
        user = self.getUserById(id)
        timeline = self.getTimelineById(id)

        try:
            if int(user['statuses_count']) > 10:
                for i in range(0, 10):
                    if 'retweeted_status' in utility_func.parse2json(timeline[i]):
                        retweets.append(timeline[i]['retweeted_status']['id'])
                    else:
                        continue
            else:
                for i in range(0, int(user['statuses_count'])):
                    if 'retweeted_status' in utility_func.parse2json(timeline[i]):
                        retweets.append(timeline[i]['retweeted_status']['id'])
                    else:
                        continue

            if int(utility_func.load_json('./config/twitter-config.json')['retweet-id']) in retweets:
                return True
            else:
                return False
        except tweepy.TweepError as error:
            print (f"[!] error captured: {error.api_code}")
            pass

    ##########################################################
    ## POST FUNCTIONS ########################################
    # return date of when the account was created
    def creation_date(self, handle):
        return self.getUserByName(handle)['created_at']

    # return recipient id from name
    def recipient(self, handle):
        return self.getUserByName(handle)['id']

    # package and deliver 2FA through Twitter
    def send_disauth(self, twitter_id, uid):
        try:
            delivery = {
                "event": {
                    "type": "message_create",
                    "message_create": {
                        "target": {
                            "recipient_id": twitter_id
                        },
                        "message_data": {
                            "text": '🍃 2FA verification 🌳\n' + uid + ' \n\nPlease copy the 2FA verification command and submit on Discord.\n\n$verify ' + uid
                        }
                    }
                }
            }

            return self.api.send_new_direct_message(delivery)
        except tweepy.TweepError as error:
            return error.api_code