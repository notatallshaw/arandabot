'''
Created on 13 Jan 2015

@author: Damian Shaw
'''
from re import sub
from urlparse import urlparse, parse_qs
from collections import namedtuple
from datetime import datetime
try:
    import praw
except ImportError:
    print("Can't find reddit module praw please insstall. \n"
          "On Windows this would look something like: \n"
          "C:\Python27\Scripts>pip2.7.exe install praw")
    raise


class redditsubmissions(object):
    def __init__(self, settings):
        self.records = {}
        self.set = settings
        self.reddit = self.getReddit()

    def getReddit(self):
        """Get a reference to Reddit."""
        r = praw.Reddit(user_agent=self.set.ua)
        try:
            r.login(self.set.username, self.set.password)
        except:
            print("Failed to login to Reddit")
            raise
        else:
            return r

    def appendYTPost(self, YTid=None, date=None):
        """Add to a collection of YouTube Posts made in this subreddit"""
        redditReccord = namedtuple('redditReccord', ["YTid", "date"])
        self.records[YTid] = redditReccord(YTid=YTid, date=date)

    def getYouTubeURLs(self, no_older_than=None):
        subr = self.reddit.get_subreddit(self.set.subreddit)
        for i, subm in enumerate(subr.get_new(limit=1000)):
            submtup = urlparse(subm.url)
            domain = submtup.netloc.lower()
            if 'youtube' in domain:
                try:
                    key = parse_qs(submtup.query)['v'][0]
                except:
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
        subr = self.reddit.get_subreddit(self.set.subreddit)
        try:
            subr.submit(title, url=link)
        except praw.errors.APIException:
            print("API error [", err.error_type), "]:", err.message,
                "while submitting ", link)
        else:
            print "Successfully submitted " + title

    def deleteAllPosts(self):
        subr = self.reddit.get_subreddit(self.set.subreddit)
        for submission in subr.get_new(limit=1000):
            try:
                submission.delete()
            except:
                print "Failed to delete: " + str(submission)
            else:
                print "Succeeded deleting: " + str(submission)
        print "Done!"
