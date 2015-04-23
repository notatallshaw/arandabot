'''
Created on 17 Mar 2015

@author: Damian Shaw [@notatallshaw]

I would like to thank Aaron C Hall [@aaronchall] for fixing a very difficult
to spot bug in calling the oauth modules that was stopping me from publishing
'''

import arandabot
import botsettings
import time


def main():
    settings = botsettings.botsettings()

    while True:
        try:
            arandabot.arandabot(settings=settings)
        except Exception, e:
            print("Some unexpected exception occured in arandabot"
                  " backing off for 5 mins and trying again:\n%s" % e)
            time.sleep(500)
        else:
            break

    input("Press return to finish script")

if __name__ == '__main__':
    main()
