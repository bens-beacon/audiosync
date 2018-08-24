"""
    BNTP - Bens Network Time Protocol

"""

import time
import os
import ntplib

class ntp:
    OFFSET = 0

    """ 
        Constructor 
        This function will called on start.
    """
    def __init__(self, timeserver):
        global OFFSET
        try: 
            client      = ntplib.NTPClient()
            response    = client.request(timeserver, version=3)
            tn          = time.time()

            #OFFSET = response.offset
            OFFSET = tn - response.tx_time + (response.offset)
            
            print (' * BTNP - ROOT Delay {:.10f}'.format(response.root_delay))
            print (' * BTNP - OFFSET     {:.10f}'.format(response.offset))
            print (' * BTNP - TIME       {:.10f}'.format(response.tx_time))
            print (' * BTNP - System     {:.10f}'.format(tn))
            print (' * BTNP - System(af) {:.10f}'.format(tn-OFFSET))

        except:
            print (' !- Module bntp: - Could not sync with time server.')

    def setOffset(self, value):
        global OFFSET
        OFFSET += value


    def time(self):
            return time.time()-OFFSET
