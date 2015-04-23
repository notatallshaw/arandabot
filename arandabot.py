'''
Created on 12 Jan 2015

@author: Damian Shaw
'''
# Python standard modules
import time
from datetime import datetime, timedelta

# My modules
import ytvideos as ytvideos
import redditsubmissions

__all__ = ('arandabot')


def _getGlobalMinDate(settings=None):
    days_newer_than = settings.days_newer_than
    global_min_date = datetime.today() - timedelta(days=days_newer_than)

    return global_min_date


def arandabot(settings=None):
    '''Arandabot is the main running of the bot'''

    # Get settings
    script_settings = settings.script
    yt_settings = settings.youtube
    reddit_settings = settings.reddit
    seconds_to_sleep = script_settings.seconds_to_sleep

    # variable instantiation
    min_date = _getGlobalMinDate(settings=yt_settings)

    # Login to and get playlists from YouTube
    yt = ytvideos.ytvideos(settings=yt_settings, no_older_than=min_date)

    # 0.95 and 0.5 are magic numbers based on anecdotal observations
    # of slow the YouTube API is
    quota_cost = int(0.95*len(yt.channel_titles)*86400
                     / (seconds_to_sleep + 0.5))*100

    # Handle expected YouTube API quota cost
    if quota_cost > 45000000:
        print("WARNING: 50,000,000 is your maximum YouTube API daily quota"
              " limit\nYour estimated maximum cost is: %s" %
              "{:,}".format(quota_cost))
    else:
        print("50,000,000 is your maximum YouTube API daily quota limit\n"
              "Your estimated maximum cost is: %s" % "{:,}".format(quota_cost))

    # Login in to reddit
    r = redditsubmissions.redditsubmissions(settings=reddit_settings)

    # script logic
    loop_number = script_settings.number_of_loops
    while script_settings.loop_forever or loop_number > 0:
        loop_number -= 1

        number_yt_videos = yt.getNewestVideos()
        if number_yt_videos or script_settings.heartbeat:
            print("%d new YouTube videos found" % number_yt_videos)

        if yt.records:
            if script_settings.repost_protection:
                r.getYouTubeURLs(no_older_than=min_date)
                duplicate_count = yt.delKeys(r.records)
                print("%d videos already posted on Reddit" % duplicate_count)

            for YTid in sorted(yt.records, key=lambda k: yt.records[k].date):
                r.submitContent(title=yt.records[YTid].title,
                                link='https://www.youtube.com/watch?v='+YTid)

        min_date = datetime.today()
        time.sleep(seconds_to_sleep)
