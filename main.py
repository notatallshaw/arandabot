'''
Created on 17 Mar 2015

@author: Geoff
'''

import arandabot
import botsettings


def main():
    settings = botsettings.botsettings()
    arandabot.arandabot(settings=settings)

if __name__ == '__main__':
    main()
