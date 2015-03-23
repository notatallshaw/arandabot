'''
Created on 11 Jan 2015

@author: Damian
'''
import botsettings
import redditsubmissions

if __name__ == '__main__':
    s = botsettings.botsettings()
    r = redditsubmissions.redditsubmissions(s.reddit)
    r.deleteAllPosts()