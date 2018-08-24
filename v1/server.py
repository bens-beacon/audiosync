"""
    SERVER:
        - 
        -

        ...

    CODE BY BEN
"""

import  socket
import  struct
import  sys
import  time
import  argparse
import  soundfile   as sf
import  signal
import  os

from    time    import sleep
from    lib     import brtp
from    lib     import bntp    

"""
    Init my libaries.
"""
rtp     = brtp.rtp()
ntp     = bntp.ntp('pool.ntp.org')

"""
    ARGPARSE
    Use client like a typical linux tool.
"""
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('filename',                             help='audio file to be played back')
parser.add_argument('-v',   '--verbose',                    help='Show more information, live.', action='store_true')
parser.add_argument('-b',   '--blocksize',      type=int,   default=2048,   help='block size (default: %(default)s)')
parser.add_argument('-l',   '--latency',        type=int,   default=500,    help='Wait before source start to play in ms. (default: %(default)s ms)')
args = parser.parse_args()

# print if params set
if args.verbose:
    print (' # verbose is active -> show details!')
if args.blocksize != 2048:
    print (' # blocksize: {}'.format(args.blocksize))
if args.latency != 500:
    print (' # latency: {}'.format(args.latency))

"""
    create Socket for multicast
"""
multicast_group = ('224.3.29.71', 10000)
# Create the datagram socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(0.2)
# Set the time-to-live for messages to 1 so they do not go past the
ttl = struct.pack('b', 1)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
# Config the RTP-Packet -> 100 -> wavfileformat
rtp.defineRTP(0,0,0,0,100)

"""
    send(message, multicast_group)
    This function send the packages.
"""
def send(message, multicast_group):
    # Send data to the multicast group
    sent = sock.sendto(message, multicast_group)



"""
    createPacket()
"""
def createPacket():

    try:
        sended = 0
        # Open file
        with sf.SoundFile(args.filename) as f:

            filesize    = os.path.getsize(args.filename)
            data        = f.buffer_read(args.blocksize, dtype='float32')

            print (' # Samplerate: {}  Channels: {}  Blocksize: {}   Filesize: {}'.format(
                f.samplerate,f.channels,args.blocksize,filesize))

            while data:

                start =  ntp.time()

                # get data
                data = f.buffer_read(args.blocksize, dtype='int16')
                
                # timestamp
                ts = ntp.time()
                ts = rtp.tailTime(ts,args.latency)
                # build and send paket
                paket = rtp.createPacket(ts,77777,1,data)
                send(paket,multicast_group)
                
                # wait until the block is played
                timeout = float(args.blocksize) / f.samplerate

                ende =  ntp.time()
                time.sleep(timeout-(ende-start)-0.0000)

                # show
                if args.verbose:
                    sended += len(data)
                    # print and replace
                    sys.stdout.write("\r # Wait: {}   Datasize: {}  Paketsize: {}  Sended: {}/{}".format(
                        round(timeout,4), len(data), len(paket), sended,filesize))
                    sys.stdout.flush()
        
        print('\n # File sended - Closing socket!')
        sock.close()

    finally:
        pass


"""
    signal_handler(signal, frame):
    With CTRL+C you can close the client. Say Goodbye clean.
"""
def signal_handler(signal, frame):
    sock.close()
    print('\n # ... pressed CTRL +C') 
    print(' # Exit')
    sys.exit() 

signal.signal(signal.SIGINT, signal_handler)

"""
    main
"""
if __name__ == '__main__':
    createPacket()
    print(' # Exit')