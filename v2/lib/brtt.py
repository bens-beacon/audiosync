"""
    ################################################################################################
    brtt
    Its to controll the RTTs from Clients,...

    Code by Ben
    ################################################################################################
"""

import time

class rtt:

    """ 
        Constructor 
        This function will called on start.
    """
    def __init__(self):
        self.CLIENTS            = []                        # Array[0] = Address | Array[1] = RTT
        self.HIGHEST_LATENCY    = 0

    """
        ############################################################################################
        getRTT()
        * float
    """
    def getRTT(self, sock, first_addr):
        
        # mesure time
        msg = 'WANNA HAVE THE R'*64   # 1024

        time_start = time.time()
        sock.sendto(msg, first_addr)
        try:
            # wait for answer of client
            data, second_addr = sock.recvfrom(1024)
        except:
            return False
        if data == msg and first_addr == second_addr:  
            time_stop  = time.time()
            rtt = (time_stop - time_start)/2

            # multiplicate with real packet time
            #rtt = rtt * 1.0156
        
        return rtt

    """
        ############################################################################################
        addClient(ADDR,RTT)
        It add the client to a list to know which device must be feed.
        * bool
    """
    def addClient(self,ADDR,RTT):

        # remove same entry and set new
        i = 0
        b = -1
        for client in self.CLIENTS:
            ip = client[0][0]
            #if ip == ADDR[0]:
            #    print (' [ADDCLIENT] same client renove the old one ... ')
            #    b = i
            #    break
            #i +=1
        if b != -1:
            self.CLIENTS.pop(b)    

        # add client
        self.CLIENTS.append([ADDR,RTT])
        # compare RTT
        if RTT > self.HIGHEST_LATENCY:
            self.HIGHEST_LATENCY = RTT
        #print (' [ADDCLIENT] add client {} - {}'.format(ADDR,RTT))

        return True


    """
        ############################################################################################
        getHighestRTTDevice()
        This function search the client in the list with the biggest RTT and return the Number.
        * int
    """
    def getHighestRTTDevice(self):

        if len(self.CLIENTS) <= 0:
            print (' [BRTT] error -> list CLIENTS is empty !')
            return False

        latency =  0
        count   =  0
        ret     = -1

        for client in self.CLIENTS:

            if latency < client[1]:
                latency = client[1]
                ret     = count
            count +=1

        return ret

    """
        ############################################################################################
        getHighestRTTDevice()
        This function check if addr is the device withe the biggest RTT.
        * bool
    """
    def isHighestRTT(self,addr):

        if len(self.CLIENTS) <= 0:
            print (' [BRTT] error -> list CLIENTS is empty !')
            return False

        highest_rtt_device = self.getHighestRTTDevice()
        count = 0
    
        for client in self.CLIENTS:

            if client[0] == addr:
                if count == highest_rtt_device:
                    return True
                else:
                    return False

            count +=1

        return False

    """
        ############################################################################################
        updateHighesRTT(self)
    """
    def updateHighesRTT(self):

        device                  = self.getHighestRTTDevice()
        self.HIGHEST_LATENCY    = self.CLIENTS[device][1]