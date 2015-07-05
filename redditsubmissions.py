'''
Created on 13 Jan 2015

@author: Damian Shaw
'''

import time
import requests.exceptions
from re import sub
from urllib.parse import urlparse, parse_qs
from collections import namedtuple
from datetime import datetime, timedelta
from traceback import print_exception

try:
    import praw
    import OAuth2Util
except ImportError:
    print("Can't find reddit module praw please install. \n"
          "Please use the provided requirements.txt. \n"
          "On Windows this would look something like: \n"
          "C:\Python34\Scripts\pip3.4.exe install -r requirements.txt")
    raise


class redditLoginManager(object):
    def __init__(self, login_timer=None):
        self.success = None
        self.relogin = None
        if login_timer:
            # The Oauth token needs to be refreshed once an hour
            n_hours_ago = datetime.utcnow() - timedelta(hours=1)
            if login_timer < n_hours_ago:
                self.relogin = True

    def __enter__(self):
        return self

    def __exit__(self, etype, value, traceback):
        if etype is None:
            self.success = True
        elif issubclass(etype, praw.errors.HTTPException):
            print("{}: Reddit API returned {} : {}"
                  "".format(time.strftime('%x %X %z'), etype, value))
            print("Sleeping for 15 seconds and trying again")
            time.sleep(15)
        elif issubclass(etype, requests.exceptions.ReadTimeout):
            print("{}: Requests returned {} : {}"
                  "".format(time.strftime('%x %X %z'), etype, value))
            print("Sleeping for 15 seconds and trying again")
            time.sleep(15)
        else:
            print("Some unhandled exception connecting to Reddit")
            print_exception(etype, value, traceback)
            return False
        return True


class redditsubmissions(object):
    def __init__(self, settings):
        self.login_timer = datetime.utcnow()
        self.records = {}
        self.set = settings
        self.login_timer = datetime.utcnow()
        self.reddit = praw.Reddit(user_agent=self.set.ua)
        self.oauth2 = OAuth2Util.OAuth2Util(self.reddit)
        self.subreddit = self.reddit.get_subreddit(self.set.subreddit)

    def refreshRedditLogin(self):
        """Get a reference to Reddit."""
        self.login_timer = datetime.utcnow()
        self.oauth2.refresh()
        self.subreddit = self.reddit.get_subreddit(self.set.subreddit)

    def appendYTPost(self, YTid=None, date=None):
        """Add to a collection of YouTube Posts made in this subreddit"""
        redditReccord = namedtuple('redditReccord', ["YTid", "date"])
        self.records[YTid] = redditReccord(YTid=YTid, date=date)

    def getYouTubeURLs(self):
        for _ in range(100):
            with redditLoginManager(self.login_timer) as request:
                if request.relogin:
                    self.subreddit = self.refreshRedditLogin()

                new_subreddit_links = self.subreddit.get_new(limit=None)

            if request.success:
                break

        for subm in new_subreddit_links:
            submtup = urlparse(subm.url)
            domain = submtup.netloc.lower()
            if 'youtube' in domain:
                try:
                    key = parse_qs(submtup.query)['v'][0]
                except Exception:
                    pass
            elif 'youtube' in sub(r'[^a-z0-9]+', '', domain):
                # This should pick up any official youtu.be URL shortner
                key = submtup.path[1:]

            try:
                self.appendYTPost(key, subm.created_utc)
            except:
                pass

    def submitContent(self, title=None, link=None):
        """Submit a link to a subreddit."""
        for _ in range(10):
            with redditLoginManager(self.login_timer) as request:
                if request.relogin:
                    self.subreddit = self.refreshRedditLogin()

                self.subreddit.submit(title, url=link)

            if request.success:
                print("{}: Successfully submitted to reddit: {}"
                      "".format(time.strftime('%x %X %z'), title))
                break

    def deleteAllPosts(self):
        for _ in range(100):
            with redditLoginManager(self.login_timer) as request:
                if request.relogin:
                    self.subreddit = self.refreshRedditLogin()

                new_subreddit_links = self.subreddit.get_new(limit=None)
                for submission in new_subreddit_links:
                    submission.delete()

            if request.success:
                print("{}: Succeeded deleting: {}"
                      "".format(time.strftime('%x %X %z'), submission))
                break

        print("Done!")
