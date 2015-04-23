'''
Created on 13 Jan 2015

@author: Damian Shaw
'''

import time
from re import sub
from urlparse import urlparse, parse_qs
from collections import namedtuple
from datetime import datetime
try:
    import praw
except ImportError:
    print("Can't find reddit module praw please install. \n"
          "Please use the provided requirements.txt. \n"
          "On Windows this would look something like: \n"
          "C:\Python27\Scripts>pip2.7.exe install -r requirements.txt")
    raise


class redditsubmissions(object):
    def __init__(self, settings):
        self.records = {}
        self.set = settings
        self.reddit = self.getReddit()
        self.subreddit = self.reddit.get_subreddit(self.set.subreddit)

    def getReddit(self):
        """Get a reference to Reddit."""
        r = praw.Reddit(user_agent=self.set.ua)
        counter = 0
        while counter < 10:
            counter += 1
            try:
                r.login(self.set.username, self.set.password)
            except praw.requests.exceptions.HTTPError, e:
                print("While trying to login to Reddit HTTPError "
                      " %d occurred:\n%s" % (e.resp.status, e.content))
                time.sleep(15)
            except Exception:
                print("Failed to login to Reddit")
                raise
            else:
                return r

    def appendYTPost(self, YTid=None, date=None):
        """Add to a collection of YouTube Posts made in this subreddit"""
        redditReccord = namedtuple('redditReccord', ["YTid", "date"])
        self.records[YTid] = redditReccord(YTid=YTid, date=date)

    def getYouTubeURLs(self, no_older_than=None):
        counter = 0
        while counter < 100:
            counter += 1
            try:
                new_subreddit_links = self.subreddit.get_new(limit=1000)
            except praw.errors.APIException, e:
                print("While trying to get subreddit links got "
                      "API error [ %s ]: %s" % (e.error_type, e.message))
                return None
            except praw.requests.exceptions.ConnectionError, e:
                print("Reddit connection error, backing off for 2 mins"
                      ":\n%s" % e)
                time.sleep(120)
            except Exception, e:
                print("Some unexpected exception submitting to reddit"
                      " sleeping for 4 mins:\n%s" % e)
                time.sleep(240)
            else:
                break

        for i, subm in enumerate(new_subreddit_links):
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

            # Test if we don't need any more data from reddit at end of
            # api "block", e.g api will throttle to 100 posts per 3 seconds
            date_posted = datetime.utcfromtimestamp(subm.created_utc)
            min_date = min(no_older_than, date_posted)
            next_position_in_block = (i + 1) % self.set.praw_block_size
            if next_position_in_block == 0 and no_older_than > min_date:
                break

    def submitContent(self, title=None, link=None):
        """Submit a link to a subreddit."""
        counter = 0
        while counter < 10:
            counter += 1
            try:
                self.subreddit.submit(title, url=link)
            except praw.errors.APIException, e:
                print("Reddit API error [ %s ]: %s while submitting %s" %
                      (e.error_type, e.message, link))
                break
            except praw.requests.exceptions.ConnectionError, e:
                print("Reddit connection error, backing off for 2 mins"
                      ":\n%s" % e)
                time.sleep(120)
            except Exception, e:
                print("Some unexpected exception submitting to reddit"
                      " sleeping for 4 mins:\n%s" % e)
                time.sleep(240)
            else:
                print("Successfully submitted %s" % title)
                break

    def deleteAllPosts(self):
        counter = 0
        while counter < 100:
            counter += 1
            try:
                new_subreddit_links = self.subreddit.get_new(limit=1000)
            except praw.errors.APIException, e:
                print("While trying to get subreddit links got "
                      "API error [ %s ]: %s" % (e.error_type, e.message))
                return None
            except praw.requests.exceptions.ConnectionError, e:
                print("Reddit connection error, backing off for 2 mins"
                      ":\n%s" % e)
                time.sleep(120)
            except Exception, e:
                print("Some unexpected exception submitting to reddit"
                      " sleeping for 4 mins:\n%s" % e)
                time.sleep(240)
            else:
                break

        for submission in new_subreddit_links:
            try:
                submission.delete()
            except Exception:
                print("Failed to delete: %s" % submission)
            else:
                print("Succeeded deleting: %s" % submission)
        print("Done!")
