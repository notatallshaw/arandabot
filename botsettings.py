'''
Created on 11 Jan 2015

@author: Damian Shaw
'''
import json
from collections import namedtuple


class botsettings(object):
    """Load the settings file for the script"""
    def __init__(self, settingsFile="settings.json"):
        settings = self.loadsettingsfromfile(settingsFile)
        self.youtube = self.youtubesettings(settings)
        self.reddit = self.redditsettings(settings)
        self.script = self.scriptSettings(settings)

    def loadsettingsfromfile(self, settingsFile):
        with open(settingsFile, "r") as f:
            try:
                settingStr = f.read()
            except IOError:
                print("Could not find settings file, getting out of here!")
                raise

        try:
            settings = json.loads(settingStr)
        except ValueError:
            print("That wasn't a JSON file you provided, getting out of here!")
            raise

        return settings

    def youtubesettings(self, settings):
        try:
            youtube = settings["youtube"]
        except KeyError:
            print("There is no 'youtube' settings in your settings file")
            raise

        try:
            accounts = youtube["accounts"]
        except KeyError:
            accounts = []

        try:
            account_ids = youtube["account_ids"]
        except KeyError:
            account_ids = []

        try:
            days_newer_than = youtube["days_newer_than"]
        except KeyError:
            days_newer_than = None

        try:
            subscriptions = youtube["subscriptions"]
        except KeyError:
            subscriptions = False

        if accounts is None and not subscriptions:
            raise TypeError("No accounts listed or subscription"
                            "pulls requested")

        try:
            title_must_contain = youtube["title_must_contain"]
        except KeyError:
            title_must_contain = None

        try:
            description_must_contain = youtube["description_must_contain"]
        except KeyError:
            description_must_contain = None

        try:
            days_uploaded_after = youtube["days_uploaded_after"]
        except KeyError:
            days_uploaded_after = 15

        youtubesettings = namedtuple('youtubesettings',
                                     ["accounts", "days_newer_than",
                                      "account_ids", "subscriptions",
                                      "title_must_contain",
                                      "description_must_contain",
                                      "days_uploaded_after"])

        return youtubesettings(
            accounts=accounts, days_newer_than=days_newer_than,
            account_ids=account_ids, subscriptions=subscriptions,
            title_must_contain=title_must_contain,
            description_must_contain=description_must_contain,
            days_uploaded_after=days_uploaded_after
            )

    def redditsettings(self, settings):
        try:
            reddit = settings["reddit"]
        except KeyError:
            print("There is no 'reddit' settings in your settings file")
            raise

        try:
            subreddit = reddit["subreddit"]
        except KeyError:
            print("There is no 'subreddit' listed in the reddit settings")
            raise

        try:
            ua = reddit["ua"]
        except KeyError:
            ua = "hello i be a bot"

        try:
            praw_block_size = reddit["praw_block_size"]
        except KeyError:
            praw_block_size = 100

        redditsettings = namedtuple('redditsettings',
                                    ["subreddit", "ua", "praw_block_size"])

        return redditsettings(subreddit=subreddit,
                              ua=ua,
                              praw_block_size=praw_block_size)

    def scriptSettings(self, settings):
        try:
            script = settings["script"]
        except KeyError:
            pass

        try:
            repost_protection = script["repost_protection"]
        except KeyError:
            repost_protection = True

        try:
            loop_forever = script["loop_forever"]
        except KeyError:
            loop_forever = True

        try:
            seconds_to_sleep = script["seconds_to_sleep"]
        except KeyError:
            seconds_to_sleep = 30

        try:
            number_of_loops = script["number_of_loops"]
        except KeyError:
            number_of_loops = 1

        try:
            heartbeat = script["heartbeat"]
        except KeyError:
            heartbeat = True

        try:
            return_to_finish = script["return_to_finish"]
        except KeyError:
            return_to_finish = True

        scriptSettings = namedtuple('scriptSettings',
                                    ["repost_protection",
                                     "loop_forever",
                                     "number_of_loops",
                                     "seconds_to_sleep",
                                     "heartbeat",
                                     "return_to_finish"])

        return scriptSettings(repost_protection=repost_protection,
                              loop_forever=loop_forever,
                              number_of_loops=number_of_loops,
                              seconds_to_sleep=seconds_to_sleep,
                              heartbeat=heartbeat,
                              return_to_finish=return_to_finish)
