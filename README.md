# arandabot
A youtube to reddit bot based on youtube API v3

To get this bot working, do the following:

1. Install Python 2.7 and download Arandabot source code

2. Go in to the settings.json file and update the following information:
 * Your Reddit Username and Password
 * Which youtube channels you would like to add
 * If you would like the bot to pull all your subscribed channels
 * If you would like to the bot to loop forever or pull n times
 
3. Create a client_secrets.json in the directory the bot is insalled by doing the following:
  * Go to https://console.developers.google.com/project
  * Create a project if not already
  * In project go to: APIs & auth > Credentials
  * Click "Create new Client ID"
  * Choose installed application > Other
  * Click "Download JSON"
  * Name file "client_secrets.json" and put in same directory as the bot

4. Install praw and Google Python API:
  * pip install google-api-python-client
  * pip install praw

5. Run main.py in your terminal or windows command prompt (you you can copy the output) and get oauth2 webtoken
  * The console will output a Google web page you need to go to and grab the token
  * Copy and paste the token back in to console
