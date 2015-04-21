'''
Created on 12 Jan 2015

@author: Damian Shaw
'''

import httplib2
import os
import Queue
import time

try:
    from apiclient.discovery import build
    from apiclient.errors import HttpError
    from apiclient.http import BatchHttpRequest
    from oauth2client.client import flow_from_clientsecrets
    from oauth2client.file import Storage
    from oauth2client.tools import run_flow, argparser
except ImportError:
    print("Can't find google-api-python-client please insstall. \n"
          "On Windows this would look something like: \n"
          "C:\Python27\Scripts>pip2.7.exe install google-api-python-client")
    raise

from collections import namedtuple
from datetime import datetime
from httplib import ResponseNotReady

__all__ = ('ytvideos')


class ytvideos(object):
    '''Class to get information about YouTube videos from specificied
    channels playlists'''

    def __init__(self, settings=None, no_older_than=None):
        '''Set some stuff up, including initially login to youtube to
        get required channel data. This tests if the credentials
        provided are correct and throws an exception if they are not'''
        self.set = settings

        # This dictionary is a record of the new YouTube videos
        # It will map a YouTube video ID to a named tuple containing
        # the title of the video and date it was added to the upload
        # playlist
        self.records = {}
        self.record = namedtuple('record', ['title', 'date'])

        # FIFO queue used by callbacks to temporary store video info
        # before upload, youtubeId needs to be held alongside
        self.q = Queue.Queue()

        # Login to YouTube using the Google provided API
        self.youtube = self.initilize_youtube(settings)
        print('Successfully authenticated against YouTube')

        # This dictionary maps the channel id to the upload
        # playlist id, this dictionary is populated with the 2 methods
        # getUserUploadPlayLists and getSubscriptionUploadPlayLists
        self.channel_to_upload_ids = {}
        self.getUserUploadPlayLists()
        if self.set.subscriptions:
            self.getSubscriptionUploadPlayLists()
        print('Successfully got channel information from YouTube')

        # The playlist min date dictionary is updated each time the max
        # playlist date increases, this is the min date to check against
        # each playlist
        self.playlist_min_date = self.populateMinDates(
            play_list_ids=self.channel_to_upload_ids.keys(),
            min_date=no_older_than
        )
        self.playlist_latest = self.populateMinDates(
            play_list_ids=self.channel_to_upload_ids.keys(),
            min_date=no_older_than
        )

    def initilize_youtube(self, settings):
        args = argparser.parse_args()
        args.noauth_local_webserver = True

        client_secrets_file = "client_secrets.json"
        missing_secrets_message = """
        WARNING: Please configure OAuth 2.0

        By installing a client_secrets.json here:
        %s

        You can get this file by:

        1. Go to https://console.developers.google.com/project
        2. Create a project if not already
        3. In project go to: APIs & auth > Credentials
        4. Click "Create new Client ID"
        5. Choose installed application > Other
        6. Click "Download JSON"
        7. Copy file to the path mentioned above
        """ % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                           client_secrets_file))

        # This OAuth 2.0 access scope allows for read-only access to the
        # authenticated user's account, but not other types of account access.
        yt_scope = "https://www.googleapis.com/auth/youtube.readonly"
        yt_api_service_name = "youtube"
        yt_api_version = "v3"

        flow = flow_from_clientsecrets(client_secrets_file,
                                       message=missing_secrets_message,
                                       scope=yt_scope)

        storage = Storage("temp-oauth2.json")
        credentials = storage.get()

        if credentials is None or credentials.invalid:
            credentials = run_flow(flow, storage, args)

        counter = 0
        while counter < 500:
            counter += 1
            try:
                youtube = build(yt_api_service_name, yt_api_version,
                                http=credentials.authorize(httplib2.Http()))
            except HttpError, e:
                print("While logging in to YouTubeaAn HTTP error"
                      " %d occurred:\n%s" % (e.resp.status, e.content))
                time.sleep(15)
            except ResponseNotReady, e:
                print("Got HTTP ResponseNotReady error when"
                      " logging in to YouTube:\n%s" % e)
                time.sleep(15)
            except httplib2.ServerNotFoundError, e:
                print("The Google API seems to not be available at the moment"
                      " with error:\n%s" % e)
                time.sleep(60)
            except Exception, e:
                print("Some unexpected exception happened when logging in to"
                      " YouTube, sleeping for 15 mins:\n%s" % e)
                time.sleep(900)
            else:
                break

        return youtube

    def populateMinDates(self, play_list_ids=None, min_date=None):
        playlist_min_date = {}

        for play_id in play_list_ids:
            playlist_min_date[play_id] = min_date

        return playlist_min_date

    def delKeys(self, keys):
        counter = 0
        for key in keys:
            try:
                del self.records[key]
            except KeyError:
                pass
            else:
                counter += 1

        return counter

    def getUserUploadPlayLists(self):
        '''Get user playlists defined in the settings file'''
        for account in self.set.accounts:
            counter = 0
            while counter < 500:
                counter += 1
                try:
                    channels_response = self.youtube.channels().list(
                        forUsername=account, part='contentDetails'
                        ).execute()
                except HttpError, e:
                    print("While getting subscriptions from YouTube an HTTP "
                          " %d occurred:\n%s" % (e.resp.status, e.content))
                    time.sleep(15)
                except ResponseNotReady, e:
                    print("Got HTTP ResponseNotReady error when"
                          "logging in to YouTube:\n%s" % e)
                    time.sleep(15)
                except httplib2.ServerNotFoundError, e:
                    print("The Google API seems to not be available at the"
                          " moment with error:\n%s" % e)
                    time.sleep(60)
                except Exception, e:
                    print("Some unexpected exception happened when logging"
                          " in to YouTube, sleeping for 5 mins:\n%s" % e)
                    time.sleep(300)
                else:
                    print("Got information for account: %s" % account)
                    break

            try:
                for item in channels_response['items']:
                    channel_id = item["id"]
                    upload_id = \
                        item['contentDetails']['relatedPlaylists']['uploads']
                    self.channel_to_upload_ids[channel_id] = upload_id
            except KeyError:
                print("There were no channels in the youtube account %s"
                      % account)

    def getSubscriptionUploadPlayLists(self):
        # Get playlists from the users subscribed channels
        nextPageToken = None
        while True:
            channel_ids = []
            # Grab 1 page of results from YouTube
            counter = 0
            while counter < 500:
                counter += 1
                try:
                    subscriber_items = self.youtube.subscriptions().list(
                        mine=True, part="snippet", maxResults=50,
                        pageToken=nextPageToken
                        ).execute()
                except HttpError, e:
                    print("While getting subscriptions from YouTube an HTTP "
                          " %d occurred:\n%s" % (e.resp.status, e.content))
                    time.sleep(15)
                except ResponseNotReady, e:
                    print("Got HTTP ResponseNotReady error when"
                          "logging in to YouTube:\n%s" % e)
                    time.sleep(15)
                except httplib2.ServerNotFoundError, e:
                    print("The Google API seems to not be available at the"
                          " moment with error:\n%s" % e)
                    time.sleep(60)
                except Exception, e:
                    print("Some unexpected exception happened when logging"
                          " in to YouTube, sleeping for 5 mins:\n%s" % e)
                    time.sleep(300)
                else:
                    break

            for item in subscriber_items["items"]:
                channel_ids.append(item["snippet"]["resourceId"]["channelId"])
                print("From subscriptions adding channel: %s" %
                      item["snippet"]["title"])

            # API only accepts at most 50 item IDs
            channels_by_comma = ",".join(channel_ids)
            counter = 0
            while counter < 500:
                counter += 1
                try:
                    channels_response = self.youtube.channels().list(
                        id=channels_by_comma, part='contentDetails'
                        ).execute()
                except HttpError, e:
                    print("While getting channel list from YouTube an HTTP"
                          " %d occurred:\n%s" % (e.resp.status, e.content))
                    time.sleep(15)
                except ResponseNotReady, e:
                    print("Got HTTP ResponseNotReady error when"
                          " getting channel list from YouTube:\n%s" % e)
                    time.sleep(15)
                except httplib2.ServerNotFoundError, e:
                    print("The Google API seems to not be available at the"
                          " moment with error:\n%s" % e)
                    time.sleep(60)
                except Exception, e:
                    print("Unexpected exception happened when getting channel"
                          " list from YouTube, sleeping for 5 mins:\n%s" % e)
                    time.sleep(300)
                else:
                    break

            try:
                for item in channels_response['items']:
                    channel_id = item["id"]
                    upload_id = \
                        item['contentDetails']['relatedPlaylists']['uploads']
                    self.channel_to_upload_ids[channel_id] = upload_id
            except KeyError:
                # This Channel was already defined by the user
                pass

            try:
                nextPageToken = subscriber_items["nextPageToken"]
            except KeyError:
                # Reached end of list
                break

    def getChannelNewestVideosCallback(self, request_id, response, exception):
        if exception is not None:
            print(exception)
        else:
            # Loop through results and add new videos to queue
            number_of_new_videos = 0
            keep_going = True

            # Sort, in case the playlist is not in reverse chronological order
            for item in sorted(response['items'],
                               key=lambda item:
                               datetime.strptime(item['snippet']["publishedAt"],
                                                 "%Y-%m-%dT%H:%M:%S.000Z"),
                               reverse=True):

                snippet = item["snippet"]
                cid = snippet["channelId"]
                channelTitle = snippet["channelTitle"]
                published = datetime.strptime(snippet["publishedAt"],
                                              "%Y-%m-%dT%H:%M:%S.000Z")

                # Check if the video is older than the filter date
                if (self.playlist_min_date[cid] is not None and
                        published <= self.playlist_min_date[cid]):
                    keep_going = False
                else:
                    number_of_new_videos += 1
                    YTid = item["id"]["videoId"]
                    title = snippet["title"]
                    date = snippet["publishedAt"]
                    self.q.put([YTid, self.record(title=title, date=date)])

                    # Update latest published timestamp for that playlistId
                    if published > self.playlist_latest[cid]:
                        self.playlist_latest[cid] = published

                if not keep_going:
                    self.playlist_min_date[cid] = self.playlist_latest[cid]
                    if number_of_new_videos:
                        print("Got %d new videos from channel: %s" %
                              (number_of_new_videos, channelTitle))
                    break

    def getNewestVideos(self):
        # Temporary fix to overcome oauth expiries, should only call once oauth
        # is expired (to be fixed)
        self.youtube = self.initilize_youtube(self.set)

        # When subscription count is large it's important to batch all the
        # HTTP requests together as 1 http request. This will break if
        # Channel list is > 1000 (to be fixed)
        batch = BatchHttpRequest(callback=self.getChannelNewestVideosCallback)

        # Add each playlist to the batch request
        for channel_id in self.channel_to_upload_ids:

            # We should be getting videos directly off the playlist items
            # But YouTube API takes 15 - 60 mins to update this list
            # So instead search.list is used at great quota cost
            batch.add(
                self.youtube.search().list(
                    part='snippet', maxResults=50, channelId=channel_id,
                    type='video', order='date', safeSearch='none'
                    )
                )

        counter = 0
        while counter < 500:
            counter += 1
            try:
                batch.execute()
            except HttpError, e:
                print("While doing a batch request to YouTube HTTP Error"
                      " %d occurred:\n%s" % (e.resp.status, e.content))
                time.sleep(15)
            except ResponseNotReady, e:
                print("Got HTTP ResponseNotReady error when"
                      " running a batch request against YouTube:\n%s" % e)
                time.sleep(15)
            except httplib2.ServerNotFoundError, e:
                print("The Google API seems to not be available at the moment"
                      " with error:\n%s" % e)
                time.sleep(60)
            except Exception, e:
                print("Some unexpected exception happened when running a batch"
                      " request against YouTube, sleeping for 5 mins:\n%s" % e)
                time.sleep(300)
            else:
                break

        counter = 0
        while not self.q.empty():
            try:
                [YTid, record] = self.q.get()
                self.records[YTid] = record
                counter += 1
            except:
                break
        if counter > 0:
            print("%d new YouTube videos ready to upload" % counter)
