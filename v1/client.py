"""
    CLIENT:
        -

        ...

    CODE BY BEN
"""

# standardlibaries
from __future__ import division
import socket
import struct
import sys
import thread
import argparse
import signal
import time         as tz
import sounddevice  as sd
# import my libaries
from   lib      import brtp
from   lib      import bntp    


"""
    Init my libaries.
"""
rtp     = brtp.rtp()

"""
    ARGPARSE
    Use client like a typical linux tool.
"""
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('-sd',  '--showdevice',   action='store_true',              help='Show all outputdevices.')
parser.add_argument('-v',   '--verbose',      action='store_true',              help='Show more information, live.', )
parser.add_argument('-d',   '--device',       type=int,                         help='Indicate the index of your sound device.')
parser.add_argument('-si',  '--syninterval',  type=int, default=50000,          help='Synchronisationinterval - after how many packages it will synchronize. Default: %(default)s', )
parser.add_argument('-bs',  '--buffersize',   type=int, default=200,            help='Buffersize - default is %(default)s Packages.')
parser.add_argument('-tw',  '--timewaste',    type=int, default=0,              help='Inaccuracy in microseconds... ')
parser.add_argument('-ts',  '--timeserver',   type=str, default='pool.ntp.org', help='Timeserver - deafult is %(default)s')
args = parser.parse_args()

# show parameter changes
if args.device:
    print (' # use outputdevice: {:}'.format(args.device))
    audio_device_index = args.device
if args.showdevice:
    print (sd.query_devices())
if args.syninterval != 200:
    print (' # synchronisationinterval: {}'.format(args.syninterval))
TIMEWASTE = 0
if args.timewaste != 0:
    TIMEWASTE = args.timewaste / 2
    print (' # timewaste: {}'.format(TIMEWASTE))

ntp     = bntp.ntp(args.timeserver)
#ntp.setOffset(-0.012)
"""
    GLOBALS
    These are all variables which are used to out of threads.
"""
BUFFER          = []
LOST            = 0             # Count lost packages.
PAKET_SIZE      = 32768         # Start paketsize, after first paket it will adapt.

"""
    Multicast
    Connect to Multicastaddress. 
"""
# Config Multicastgroup
multicast_group = '224.3.29.71'
server_address = ('', 10000)
# Create the socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#sock.settimeout(1)
sock.bind(server_address)
group = socket.inet_aton(multicast_group)
mreq = struct.pack('4sL', group, socket.INADDR_ANY)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

"""
    RECEIVE - Thread
    It will receive packages and fill the Buffer.
"""
def RECEIVE():

    global BUFFER
    global PAKET_SIZE
    global LOST
    seqnum_prev = 0

    while True:

        # Bufferlimit
        while len(BUFFER) > args.buffersize:
            #BUFFER.pop(0)
            print (' # !!! Buffer overflows')
            sys.exit()

        try:
            data, address   = sock.recvfrom(PAKET_SIZE+16)
            PAKET_SIZE      = len(data)-16                  # adapt PAKET_SIZE
        except:
            print (' # !!! Socketfailure')
            sys.exit()

        # check for lost packages
        if len(BUFFER) > 0:
            seqnum, paket = rtp.getData(data)
         
            if seqnum != seqnum_prev+1:
                LOST +=1
                #BUFFER.append(data)
            seqnum_prev = seqnum 
     
        BUFFER.append(data)
    
"""
    CONTROL - Thread
    It controls the stream. Open, Close and set new. It takes the first paket from Buffer and use
    the params to set the Stream.
"""
def CONTROL():

    first_package = True
    
    while True:
        
        if len(BUFFER) > 0 and first_package:
            
            data = BUFFER[0]
           
            # init outputstream take typw from first package
            seqnum, packet  = rtp.getData(data)
            payloadtype     = packet['payloadtype']
            info            = rtp.getPayloadInfos(payloadtype)

            # set stream
            block_size = 2048
            print (' # Payloadsize: {}  Blocksize: {}   Samplerate: {}'.format(PAKET_SIZE, block_size, info['rate']))

            try:
                with sd.RawOutputStream(
                    device              = args.device,
                    samplerate          = info['rate'],
                    blocksize           = block_size,
                    dtype               = 'int16',        # info['type']
                    channels            = info['channels'],
                    callback            = callback
                    ):
                    while len(BUFFER) > 0:
                        pass
            except:
                print(' # !!! Streamfailure')
                sys.exit()

            first_package = False

        elif len(BUFFER) == 0 and not(first_package):
            first_package = True
        
        else:
            # wait for new packages
            tz.sleep(0.5)
            
    print (' # !!! CONTROL -> go out')

"""
    callback(in_data, frame_count, time_info, status)
    It take the first object from buffer and compares his own time with pakettime. If euqal then 
    play. If not, then wait or go faster. 
"""
tr_average          = 0     # rest time between offset and transmission time
syninterval_count   = 0     # its for latency
SEQN                = 1
def callback(outdata, frames, time, status):

    global tr_average
    global syninterval_count
    global SEQN

    # get current time of system
    tc = ntp.time()
    tc = rtp.tailTime(tc,0)   

    # if buffer is filled
    if len(BUFFER) > 0:
        
  
        # get all important information from packet
        rtpPacket       = BUFFER.pop(0)
        seqnum, paket   = rtp.getData(rtpPacket)
        tp              = paket['timestamp']
        data            = paket['payload']

        # when paket lost, then new sync
        if seqnum != SEQN:
            SEQN = seqnum
            syninterval_count = 1

        SEQN +=1

        # sync
        if seqnum % args.syninterval == 0 or syninterval_count < 2:

            # calc tu
            syninterval_count +=1
            tr = tp - tc                                           # tr is later transmission time 
            tr_average = float(tr+tr_average)/2
            #tc = tc + tr_average
            print (' # COUNT: {} | tp-tc: {}ms | average: {} diff: {}'.format(syninterval_count,tr/1000,tr_average/1000,(tp-tc)/1000))    
           
            # syn slow and fast
            while not(tp >= tc-TIMEWASTE and tp <= tc+TIMEWASTE):
                
                # wait
                if tp > tc:
                    print (' # - wait')
                    while (tp > tc):
                        
                        tc = ntp.time()
                        tc = rtp.tailTime(tc,0)
                        
                    break
                        
                # go fast
                elif tp < tc:
                    print (" # - fast")
                    # get all important information from packet
                    if len(BUFFER) > 0:
                        rtpPacket       = BUFFER.pop(0)
                        seqnum, paket   = rtp.getData(rtpPacket)
                        tp              = paket['timestamp']
                        data            = paket['payload']       
                    else:
                        break                                      


        outdata[:] = data


"""
    STATE(): -> its a Thread
    It show bufferlen and lost packages.
"""
def STATE():
    
    print(' # -v -> show STATE:')
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
    signal_handler(signal, frame):
    With CTRL+C you can close the client. Say Goodbye clean.
"""
def signal_handler(signal, frame):
    #sock.close()
    print('\n # ... pressed CTRL +C     -> EXIT')
    sys.exit() 

signal.signal(signal.SIGINT, signal_handler)

"""
    MAIN
    If enter the main thread with all other will exit.
"""
if __name__ == '__main__':

    thread.start_new_thread(RECEIVE,())                             # received packages
    thread.start_new_thread(CONTROL,())                             # control stream

    if args.verbose:                                                # show state
        thread.start_new_thread(STATE,())

    c = raw_input(" # to EXIT press Enter! \n")
    #sock.close()
    print('\n # ... pressed ENTER     -> EXIT')
