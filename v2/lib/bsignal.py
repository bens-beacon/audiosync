"""
    ################################################################################################
    bsignal
    It is just a Signalhandler to exit the running process with CTRL+C. Or maybe more...

    Code by Ben
    ################################################################################################
"""

"""
    Imports:
"""
import signal
import sys

"""
    ################################################################################################
    signal_handler(signal, frame):
    Exit with CTRL+C.
"""
def signal_handler(signal, frame):
    #sock.close()
    print('\n [BSIGNAL] hard Exit \n')
    sys.exit() 

signal.signal(signal.SIGINT, signal_handler)