

import time
import datetime
import sys

from   lib import bntp   

ntp     = bntp.ntp('pool.ntp.org')                            # sync time 

while True:

    tn = ntp.time()

    #st = datetime.datetime.fromtimestamp(tn).strftime('\r %Y-%m-%d %H:%M:%S')

    st = '\r {:.10f}'.format(tn)

    sys.stdout.write(st)
    sys.stdout.flush()