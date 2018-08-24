"""
    ################################################################################################
    CLIENT V2

    Problems:
        - blocksize should control by program not by hand
        - play lost packages again

    Code by Ben
    ################################################################################################
"""

from __future__ import division
import socket
import struct
import sys
import thread
import argparse
import time         as tz
import sounddevice  as sd

from   lib    import brtp
from   lib    import bsignal

"""
    Init my libaries.
"""
rtp     = brtp.rtp()                            # for rtp packages
rtp.defineRTP(0,0,0,0,100)
"""
    ARGPARSE
    Use client like a typical linux tool.
"""
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('-sd',  '--showdevice',                 help='Print index of all audio devices.', action='store_true')
parser.add_argument('-v',   '--verbose',                    help='Show more information, live.', action='store_true')
parser.add_argument('-d',   '--device',         type=int,   help='Indicate the index of your sound device.')
parser.add_argument('-b',   '--blocksize',      type=int,   help='block size (default: %(default)s)',default=2048)
parser.add_argument('-s',   '--server',         type=str,   help='Need the address of the server', default='localhost')
parser.add_argument('-p',   '--port',           type=int,   help='Port of server.', default=10000)
parser.add_argument('-l',   '--low',            type=float, help='Time what device is slower', default=0)
args = parser.parse_args()

# show parameter changes
if args.device:
    print (' [ARGPARSE] use outputdevice: {:}'.format(args.device))
    audio_device_index = args.device
if args.showdevice:
    print (sd.query_devices())

"""
    ################################################################################################
    RECEIVE()
    Connect with server and receive audio content.
"""
BUFFER          = []                            # contain actually just one paket
PAKET_SIZE      = 32768                         # Start paketsize, after first paket it will adapt.
COUNTER         = 0
LOST            = 0                             # interessting for wlan
INITTIME        = 0
def RECEIVE():

    global LOST
    global COUNTER
    global BUFFER
    global PAKET_SIZE

    msg = 'WANNA HAVE THE R'*64   # 1024

    # start with connection 
    sock.sendto('WANNA CONNECT TO SERVER', (args.server, args.port))
    
    # connection mode ##############################################################################
    while True:

        # wait for answer of server
        try:
            data, first_addr    = sock.recvfrom(PAKET_SIZE)
        except:
            print (' [RECEIVE] something went wrong, try to connect again!')
            sock.sendto('WANNA CONNECT TO SERVER', (args.server, args.port))
            continue

        # wait processing time and send message back
        if data == msg:
            tz.sleep(INITTIME*2 + args.low*2)           
            # send rtt request
            sock.sendto(data,(args.server, args.port))     

        # if everything was good
        if len(BUFFER) == 0:
            data, second_addr = sock.recvfrom(PAKET_SIZE)
            if data == 'RTT DONE' and first_addr == second_addr:
                print (' [RECEIVE] connection successfull')
                break

    # normal receive mode ##########################################################################
    prev_data = 0
    while True:
        try:
            data, first_addr    = sock.recvfrom(PAKET_SIZE)
        except:
            continue

        if data == 'WANNA HAVE THE RTT': 
            sock.sendto(data,(args.server, args.port))              # send rtt request

        else:

            ########################################################################################
            ###### TEST PART #######################################################################
            #if COUNTER == 0:
            #    sock.sendto(data,(args.server, args.port))
            ########################################################################################
            ###### TEST PART #######################################################################

            # count lost packages
            seqnum, paket   = rtp.getData(data)
            if seqnum != COUNTER:
                LOST +=1
                COUNTER = seqnum
                if prev_data != 0:
                    BUFFER.append(data)
            COUNTER += 1

            # normal 
            BUFFER.append(data)
            prev_data = data
            PAKET_SIZE          = len(data)                         # adapt paketsize
            
            
    
"""
    ################################################################################################
    PLAY()
    This thread starts and stop and set the stream.
"""
def PLAY():

    while True:
        if len(BUFFER) > 5:
            
            data = BUFFER[0]                            # get first paket from buffer
           
            # init outputstream take typw from first package
            seqnum, packet  = rtp.getData(data)
            payloadtype     = packet['payloadtype']
            info            = rtp.getPayloadInfos(payloadtype)

            print (' [PLAY] Payloadsize: {}  Blocksize: {}   Samplerate: {}  Channel: {}'.format(
                    PAKET_SIZE, args.blocksize, info['rate'], info['channels']))

            with sd.RawOutputStream(
                device              = args.device,
                samplerate          = info['rate'],
                blocksize           = args.blocksize,   # its 
                dtype               = 'int16',          # info['type']
                channels            = info['channels'],
                latency             = 'high',           # its to have on every device same latency
                callback            = callback
            ):
                while FAIL_COUNTER < 1:                 # after 5 fails -> break
                    pass

        else:
            pass

"""
    ################################################################################################
    callback()
    Its the sounddevice callback function...
"""
FAIL_COUNTER    = 0                                 # count series of fails       
def callback(outdata, frames, time, status):
    
    global FAIL_COUNTER
    played = False

    # if buffer is filled
    while not(played):
        
        played          = True

        if len(BUFFER) > 0:
        
            # get all important information from packet
            rtpPacket       = BUFFER.pop(0)
            seqnum, paket   = rtp.getData(rtpPacket)
            data            = paket['payload']
            outdata[:]      = data                      # put to stream
            FAIL_COUNTER    = 0                         # reset fails

        else:
            outdata[:] = b'\x00' * (2*args.blocksize)
            print (' [CALLBACK] ... nothing to play')
            FAIL_COUNTER += 1



"""
    ################################################################################################
    STATE(): -> its a Thread
    It show bufferlen and lost packages.
"""
def STATE():
    
    print(' [STATE] -v -> show STATE:')
    while True:

        buffer_length   = len(BUFFER)
        # print package infos
        if buffer_length > 0:

            # print and replace
            sys.stdout.write("\r # Buffer: {} | Lost Packages: {}".format(buffer_length, LOST))
            sys.stdout.flush()
        
        # wait
        tz.sleep(0.5)  

"""
    ################################################################################################
    INIT
    Simulate time which need to start play with first package.
"""
def INIT():
    global INITTIME

    start       = tz.time()

    # simulate receive
    buffer      = []
    for i in range(1,68):

        data            = b'\x00' * 4112
        paket           = rtp.createPacket(1,77777,1,data)
        seqnum, data    = rtp.getData(paket)
        
        if data == 'WANNA HAVE THE RTT':
            pass
        else:
            buffer.append(data)

        outdata         = []
        seqnum, paket   = rtp.getData(paket)   
        data            = paket['payload']
        outdata[:]      = data                      # put to stream
        FAIL_COUNTER    = 0                         # reset fails

    # simulate play
    while len(buffer) > 0:
        prev        = buffer.pop(0)
        prev_len    = len(prev)

    # sleep sound latency
    if not(args.device):
        device_latency  = sd.query_devices(0)['default_high_output_latency']
    else:    
        device_latency  = sd.query_devices(args.device)['default_high_output_latency']
    tz.sleep(device_latency*2)

    end         = tz.time()
    INITTIME    = end-start

    print (' [INIT] device latency: {}'.format(device_latency))
    print (' [INIT] processing time: {}'.format(INITTIME+args.low))   
    

"""
    ################################################################################################
    MAIN
"""
if __name__ == '__main__':
    
    print (' ########- CLIENT -######## ')
    print (' [MAIN] dry to connect to {} : {}'.format(args.server,args.port))

    # init time 
    INIT()

    # make a request to server
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
    sock.settimeout(3)
    
    # threads
    thread.start_new_thread(RECEIVE,())
    thread.start_new_thread(PLAY,())

    if args.verbose:                                                # show state
        thread.start_new_thread(STATE,())

    # control
    while True:
        c = raw_input(" [MAIN] CONTROL: c - EXIT\n")

        if c == 'c':
            print (' [MAIN] hard Exit \n')
            sys.exit()
    



            