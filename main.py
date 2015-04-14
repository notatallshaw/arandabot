'''
Created on 17 Mar 2015

@author: Damian Shaw [@notatallshaw]

I would like to thank Aaron C Hall [@aaronchall] for fixing a very difficult
to spot bug in calling the oauth modules that was stopping me from publishing
'''

import arandabot
import botsettings


def main():
    settings = botsettings.botsettings()
    arandabot.arandabot(settings=settings)

if __name__ == '__main__':
    main()
