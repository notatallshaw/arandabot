'''
Created on 12 Jan 2015

@author: Damian Shaw
'''

import httplib2
import os

try:
    from apiclient.discovery import build
    from apiclient.errors import HttpError
except ImportError:
    print("Can't find google-api-python-client please insstall. \n"
          "On Windows this would look something like: \n"
          "C:\Python27\Scripts>pip2.7.exe install google-api-python-client")
    raise

from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run_flow, argparser
from collections import namedtuple
from datetime import datetime

__all__ = ('ytvideos', 'HttpError')


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
            play_list_ids=self.channel_to_upload_ids.values(),
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

        youtube = build(yt_api_service_name,
                        yt_api_version,
                        http=credentials.authorize(httplib2.Http()))

        return youtube

    def populateMinDates(self, play_list_ids=None, min_date=None):
        playlist_min_date = {}

        for play_id in play_list_ids:
            playlist_min_date[play_id] = min_date

        return playlist_min_date

    def delKeys(self, keys):
        for key in keys:
            try:
                del self.records[key]
            except KeyError:
                pass

    def getUserUploadPlayLists(self):
        '''Get user playlists defined in the settings file'''
        for account in self.set.accounts:
            print("Getting information for channel: " + account)
            channels_response = self.youtube.channels().list(
                forUsername=account,
                part='contentDetails'
                ).execute()
            try:
                for item in channels_response['items']:
                    channel_id = item["id"]
                    upload_id = \
                        item['contentDetails']['relatedPlaylists']['uploads']
                    self.channel_to_upload_ids[channel_id] = upload_id
            except KeyError:
                print("There were no channels in the youtube account "
                      + account)

    def getSubscriptionUploadPlayLists(self):
        # Get playlists from the users subscribed channels
        nextPageToken = None
        while True:
            channel_ids = []
            # Grab 1 page of results from YouTube
            subscriber_items = self.youtube.subscriptions().list(
                mine=True, part="snippet", maxResults=50,
                pageToken=nextPageToken
                ).execute()

            for item in subscriber_items["items"]:
                channel_ids.append(item["snippet"]["resourceId"]["channelId"])
                print("From subscriptions adding channel: " +
                      item["snippet"]["title"])

            # API only accepts at most 50 item IDs
            channels_by_comma = ",".join(channel_ids)
            channels_response = self.youtube.channels().list(
                id=channels_by_comma, part='contentDetails'
                ).execute()

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

    def getChannelNewestVideo(self, playlistId=None):
        next_page_token = None
        keep_going = True
        number_of_new_videos = 0
        # Get current playlist min date as the function can update
        # this value
        current_playlist_min_date = self.playlist_min_date[playlistId]

        while True:
            # Grab 1 page of results from YouTube at a time
            playlist_snippet = self.youtube.playlistItems().list(
                playlistId=playlistId, part='snippet',
                maxResults=50, pageToken=next_page_token
                ).execute()

            # Loop through results and populate dictionary
            for item in playlist_snippet["items"]:
                snippet = item["snippet"]
                channelTitle = snippet["channelTitle"]
                published = datetime.strptime(snippet["publishedAt"],
                                              "%Y-%m-%dT%H:%M:%S.000Z")

                # Check if the video is older than the filter date
                if (current_playlist_min_date is not None and
                        published <= current_playlist_min_date):
                    keep_going = False
                else:
                    YTid = snippet["resourceId"]["videoId"]
                    title = snippet["title"]
                    date = snippet["publishedAt"]
                    self.records[YTid] = self.record(title=title, date=date)
                    number_of_new_videos += 1

                # Check if the playlist min date can be increased
                if (self.playlist_min_date[playlistId] is None or
                        published > self.playlist_min_date[playlistId]):
                    self.playlist_min_date[playlistId] = published

            if not keep_going:
                if number_of_new_videos:
                    print("Got " + str(number_of_new_videos) +
                          " new videos from channel: " + channelTitle)
                break
            try:
                next_page_token = playlist_snippet['nextPageToken']
            except KeyError:
                # Reached end of list
                break

    def getNewsestVideos(self):
        for channel, play_list_id in self.channel_to_upload_ids.items():
            try:
                self.getChannelNewestVideo(playlistId=play_list_id)
            except HttpError,e:
                print("HttpError " + str(e.resp.status) +
                      " occurred when polling Channel " + channel +
                      "\nDetails:\n" + str(e.content))
