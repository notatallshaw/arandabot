'''
Created on 17 Mar 2015

@author: Damian Shaw [@notatallshaw]

I would like to thank Aaron C Hall [@aaronchall] for fixing a very difficult
to spot bug in calling the oauth modules that was stopping me from publishing
'''

import arandabot
import botsettings
import time
import traceback

def main():
    settings = botsettings.botsettings()

    while True:
        try:
            arandabot.arandabot(settings=settings)
        except ImportError:
            print("Import Error")
            break
        except Exception as e:
            print("{} Some unexpected exception occurred in arandabot "
                  "backing off for 5 mins and trying again:"
                  " {}".format(time.strftime('%x %X %z'), e))
            traceback.print_exc()
            time.sleep(300)
        else:
            break

    if settings.script.return_to_finish:
        input("Press return to finish script")

if __name__ == '__main__':
    main()
