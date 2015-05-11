'''
Created on 13 Jan 2015

@author: Damian Shaw
'''

import time
from re import sub
from urlparse import urlparse, parse_qs
from collections import namedtuple
from datetime import datetime, timedelta
from traceback import print_exception

try:
    import praw
except ImportError:
    print("Can't find reddit module praw please install. \n"
          "Please use the provided requirements.txt. \n"
          "On Windows this would look something like: \n"
          "C:\Python27\Scripts\pip2.7.exe install -r requirements.txt")
    raise


class redditLoginManager(object):
    def __init__(self, login_timer=None):
        self.success = None
        self.relogin = None
        if login_timer:
            n_hours_ago = datetime.utcnow() - timedelta(hours=6)
            if login_timer < n_hours_ago:
                self.relogin = True

    def __enter__(self):
        return self

    def __exit__(self, etype, value, traceback):
        if etype is None:
            self.success = True
        elif issubclass(etype, praw.requests.exceptions.HTTPError):
            print("Reddit API returned HTTP : %s" % (value))
            time.sleep(15)
        elif issubclass(etype, praw.requests.exceptions.ConnectionError):
            print("Reddit connection error %s, backing off for 1 min:\n"
                  "%s" % (etype, value))
            time.sleep(60)
        else:
            print("Failed to login to reddit")
            print_exception(etype, value, traceback)
            return False
        return True


class redditsubmissions(object):
    def __init__(self, settings):
        # If login was more than x hours ago, relogin
        self.login_timer = datetime.utcnow()
        self.records = {}
        self.set = settings
        self.subreddit = self.initializeReddit()

    def initializeReddit(self):
        """Get a reference to Reddit."""
        self.login_timer = datetime.utcnow()
        r = praw.Reddit(user_agent=self.set.ua)

        for _ in xrange(10):
            with redditLoginManager() as request:
                r.login(self.set.username, self.set.password)

            if request.success:
                break

        return r.get_subreddit(self.set.subreddit)

    def appendYTPost(self, YTid=None, date=None):
        """Add to a collection of YouTube Posts made in this subreddit"""
        redditReccord = namedtuple('redditReccord', ["YTid", "date"])
        self.records[YTid] = redditReccord(YTid=YTid, date=date)

    def getYouTubeURLs(self):
        for _ in xrange(100):
            with redditLoginManager(self.login_timer) as request:
                if request.relogin:
                    self.subreddit = self.initializeReddit()

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
        for _ in xrange(10):
            with redditLoginManager(self.login_timer) as request:
                if request.relogin:
                    self.subreddit = self.initializeReddit()

                self.subreddit.submit(title, url=link)

            if request.success:
                print("Successfully submitted to reddit: %s" % title)
                break

    def deleteAllPosts(self):
        for _ in xrange(100):
            with redditLoginManager(self.login_timer) as request:
                if request.relogin:
                    self.subreddit = self.initializeReddit()

                new_subreddit_links = self.subreddit.get_new(limit=None)
                for submission in new_subreddit_links:
                    submission.delete()

            if request.success:
                print("Succeeded deleting: %s" % submission)
                break

        print("Done!")
