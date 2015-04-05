'''
Created on 12 Jan 2015

@author: Damian Shaw
'''
# Python standard modules
import time
from datetime import datetime, timedelta

# My modules
import ytvideos
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

    # variable instantiation
    min_date = _getGlobalMinDate(settings=yt_settings)

    # Login to and get playlists from YouTube
    while True:
        try:
            yt = ytvideos.ytvideos(settings=yt_settings,
                                   no_older_than=min_date)
        except ytvideos.HttpError, e:
            print("An HTTP error %d occurred:\n%s" %
                  (e.resp.status, e.content))
        else:
            print("Successfully logged in to and got channel information "
                  "for YouTube")
            break

    r = redditsubmissions.redditsubmissions(settings=reddit_settings)

    # script logic
    loop_number = script_settings.number_of_loops
    while script_settings.loop_forever or loop_number > 0:
        loop_number -= 1

        yt.getNewestVideos(yt_settings)

        if yt.records:
            if script_settings.repost_protection:
                r.getYouTubeURLs(no_older_than=min_date)
                yt.delKeys(r.records)

            for YTid in sorted(yt.records, key=lambda k: yt.records[k].date):
                r.submitContent(title=yt.records[YTid].title,
                                link='https://www.youtube.com/watch?v='+YTid)

        min_date = datetime.today()
        time.sleep(script_settings.seconds_to_sleep)
