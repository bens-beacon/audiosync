"""
    ################################################################################################
    SERVER V2
    How it works:
        The Server calculate the RTTs to all connectet clients. Knowing the biggest RTT, it will 
        sends the packages to specific times. All packages schould receive at the same time.

    Problems:
        - add new client while playing

    Code by Ben
    ################################################################################################
"""

import  socket
import  struct
import  sys
import  thread
import  argparse
import  time
import  soundfile   as sf
import  os
import  thread

from    lib     import brtp
from    lib     import bsignal
from    lib     import brtt

"""
    Init my libaries.
"""
rtp             = brtp.rtp()
rtp.defineRTP(0,0,0,0,100)

rtt             = brtt.rtt()

"""
    ARGPARSE
    Use client like a typical linux tool.
"""
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('filename',                         help='audio file to be played back')
parser.add_argument('-v',  '--verbose',                 help='Show more information, live.', action='store_true')
parser.add_argument('-s',  '--server',      type=str,   help='Need the address of the server', default='localhost')
parser.add_argument('-p',  '--port',        type=int,   help='Port of server.', default=10000)
parser.add_argument('-b',  '--blocksize',   type=int,   help='block size (default: %(default)s)',default=2048)
parser.add_argument('-bs', '--buffersize',  type=int,   help='buffersize (default: %(default)s)',default=200)
parser.add_argument('-t',  '--timeout',     type=float, help='Servertimeout within clients must answer. Default is %(default)s.', default=1.5)
parser.add_argument('-tt', '--ttimeout',    type=float, help='Servertimeout to collect new rtts from clients. Its goes up linear with factor 1.1 with Default is %(default)s.', default=500.0)
args = parser.parse_args()

"""
    ################################################################################################
    CONNECTOR()
    This function connect the clients and measure the rtt. It will controlled from the Variable CONTROL_STATUS.
    It does not connect new clients while playing.
"""
PLAY = True
def CONNECTOR(UDP_IP, UDP_PORT):
    # wait for new connections
    while True:
        print (' [CONNECTOR] waiting for clients on {} : {} ...'.format(UDP_IP,UDP_PORT))

        # CONTROL_STATUS -> wait for connection
        while CONTROL_STATUS == 0:
            try:
                data, first_addr = sock.recvfrom(1024)
                # this is the typically sync task
                if data == 'WANNA CONNECT TO SERVER':  
                        rtt_time = rtt.getRTT(sock,first_addr)
                        sock.sendto('RTT DONE', first_addr)
                        print (' [CONNECTOR] got new client on {} : {} RTT: {}'.format(
                            first_addr[0],first_addr[1],rtt_time))
                        rtt.addClient(first_addr,rtt_time)
            except:
                pass
        
        # CONTROL_STATUS -> now start to play
        if CONTROL_STATUS == 1:

            thread.start_new_thread(OPENFILE,())                        # open file
            time.sleep(0.1)                                             # wait to fill ringbuffer
            thread.start_new_thread(RTTSETTER,())                       # start RTTSETTER 

            for client in rtt.CLIENTS:
                thread.start_new_thread(SENDER,(client[0],client[1]))   # open thread to send

            while CONTROL_STATUS == 1:                                  # do not close the threads
                pass

            print (' [CONNECTOR] close all Threads...')

"""
    ################################################################################################
    RTTSETTER()
    It sends RTT-inquiries and set the new RTT to the discrete client. It used the BRTT Libary. 
    There are two importand variables. RTT.HIGHEST_LATENCY, RTT.CLIENTS
    It will repeats every X seconds.
"""
SYNC            = 0                                                     # it decrease
def RTTSETTER():
    
    global SYNC
    rtt_wait_time = args.ttimeout

    print (' [RTTSETTER] collect RTTs')

    while True:
        rtt_wait_time = (rtt_wait_time*1)                               # factor 1.1x  
        time.sleep(rtt_wait_time)                                       # timeout

        # for every connection
        for client in rtt.CLIENTS:
            rtt_time = rtt.getRTT(sock,client[0])                       # get rtt 
            #print ('{} , {}'.format(client[0],rtt_time))


            if rtt == False:                                            # no answer
                print (' [RTTSETTER] no answer received from {}'.format(client[0]))
                continue

            if rtt.isHighestRTT(client[0]):                             # update specific device
                rtt.updateHighesRTT()                               
                #print (' HIGHEST {}'.format(client[0]))

            if rtt.HIGHEST_LATENCY < rtt_time:                          # set highest rtt
                rtt.HIGHEST_LATENCY = rtt_time

            client[1] = rtt_time                                        # update device list

        SYNC +=1                                                        # sync flank



"""
    ################################################################################################
    SENDER(ADDRESS, LATENZ)
    This thread will create for every connection. It sends the data to the clients. But before, it
    calculates the specific latency and wait.
"""
def SENDER(ADDRESS, LATENZ):
    
    global BUFFER
    count       = 0                                                     # for paketnum
    sync_count  = 0
    #print (' [SENDER][thread] -> {} t_: {:}'.format(ADDRESS, LATENZ))

    while True:
        if BUFFER[30] != 0:

            timeout = rtt.HIGHEST_LATENCY - LATENZ                      # waiting
            
            # if RTT was resettet
            if SYNC >= sync_count:
                sync_count += 1
                if timeout > 0:
                    print (' [SENDER][wait] %s has to wait %f' % (ADDRESS,timeout))
                    time.sleep(timeout)
                    
            # get from ringbuffer 
            index   = count % args.buffersize 
            count  +=1
            data    = BUFFER[index]

            ########################################################################################
            ###### TEST PART #######################################################################
            #if count == 1:
            #    start = time.time()
            #
            #    sock.sendto(data, ADDRESS)                                  # send
            #    try:
            #       data, first_addr = sock.recvfrom(4112)
            #    except:
            #        print ('Timout')
            #    
            #    end = time.time()
            #    f   = (4112/1024)
            #    gf  = ((end - start)/2) / f
            #
            #    #print (' [TEST] {}  {}  {}  {}'.format(ADDRESS,LATENZ,gf,LATENZ-gf))
            #    print (' [TEST] %s  %f  %f  %f' % (ADDRESS,LATENZ,gf,LATENZ-gf))
            #    time.sleep(CHUNK_TIMEOUT-gf)                                # wait
            #
            ########################################################################################
            ###### TEST PART #######################################################################


            #else:
            sock.sendto(data, ADDRESS)                                  # send
            time.sleep(CHUNK_TIMEOUT)                                   # wait
        
"""
    ################################################################################################
    OPENFILE():
    It will open the file and fill the BUFFER with the chunks. Its a ringbuffer. After a specific 
    num of packages it will start ahead. It will set the global CHUNK_TIMOUT.
"""
CHUNK_TIMEOUT = 0
def OPENFILE():
    
    global BUFFER
    global CHUNK_TIMEOUT
    count = 0                                                           # paketnum 

    try:
        with sf.SoundFile(args.filename) as f:

            filesize    = os.path.getsize(args.filename)
            data        = f.buffer_read(args.blocksize, dtype='int16')

            print (' [OPENFILE] Samplerate: {}  Channels: {}  Blocksize: {}   Filesize: {}'.format(
                f.samplerate,f.channels,args.blocksize,filesize))

            while data:
                
                start   = time.time()                                   # paket creation needs time
                data    = f.buffer_read(args.blocksize, dtype='int16')  # get data      
                paket   = rtp.createPacket(1,77777,1,data)              # build and send paket

                # write it in ringbuffer                                # BUFFER.append(paket)
                index           = count % args.buffersize 
                BUFFER[index]   = paket
                count          +=1
                end             = time.time()                           # end of creation

                # global periodtime
                CHUNK_TIMEOUT = (float(args.blocksize) / f.samplerate)  # set wait time
                time.sleep(CHUNK_TIMEOUT-(end-start))                   # pull creation time...

                #print (' [OPENFILE] Chunklength: {}'.format(CHUNK_TIMEOUT))
           
    except:
        print (' [OPENFILE] -> [ERROR] ...')


"""
    ################################################################################################
    MAIN
"""

CONTROL_STATUS  = 0                                                     # 0 stop, 1 play
BUFFER          = []                                                    # its a ringbuffer

if __name__ == '__main__':
    print (' ########- SERVER -######## ')
    
    # set Server
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
    sock.settimeout(args.timeout)
    sock.bind((args.server, args.port))

    print (' [MAIN] I\'m {} : {} '.format(sock.getsockname(),args.port))

    # init Buffer
    i = 0
    for i in range(0,args.buffersize):
        BUFFER.append(0)

    # start main thread
    thread.start_new_thread(CONNECTOR,(args.server,args.port))

    # control
    while True:
        c = raw_input(" [MAIN] CONTROL:  p - PLAY | c - EXIT\n")

        if c == 'c':
            print (' [MAIN] hard Exit \n')
            
            sys.exit()
        if c == 'p':
            if CONTROL_STATUS == 0:
                CONTROL_STATUS = 1
            else:
                CONTROL_STATUS = 0          