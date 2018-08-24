"""
    BRTP - Bens Real Time Protokoll
    Its a Class to ...

    https://github.com/sparkslabs/kamaelia/blob/master/Code/Python/Kamaelia/Kamaelia/Protocol/RTP/RTP.py

"""

import struct

class rtp:

    """ 
        Constructor 
        This function will called on start.
    """
    def __init__(self):
        self.seqnum      = 0
        self.extensionPacket = {'info','a'}

    """
        defineRTP
        Config the RTP part. All vars which will not changend normally. 
    """
    def defineRTP(self,padding,extension,csrcc,marker,payloadtype):
        self.padding     = padding
        self.extension   = extension
        self.csrcc       = csrcc
        self.marker      = marker
        self.payloadtype = payloadtype
        

    """
        showRTP
        This function should display some informations about RTP-Header or RTP Packet.
    """
    def showRTP(self):
        print self.padding

    """ 
        createPacket 
        Create a RTP Packet and return it.
    """
    def createPacket(self,timestamp,ssrc,csrcs,payload):
        packet = []
        
        byte = 0x80                         # for RTP version 2

        if self.padding: byte=byte + 0x20
        if self.extension: byte=byte + 0x10
        assert(self.csrcc<16)               # go with 15 not matter it number is higher
        byte=byte + csrcs
        
        packet.append( chr(byte) )

        byte = self.payloadtype & 0x7f
        if self.marker:
            byte = byte + 0x80

        packet.append( chr(byte) )

        packet.append( struct.pack(">H", self.seqnum) )
        self.seqnum = (self.seqnum + 1) & 0xffff

        packet.append( struct.pack(">I",timestamp) )
        packet.append( struct.pack(">I",ssrc & 0xffffffff) )
        packet.append( struct.pack(">I",csrcs & 0xffffffff) )

        if self.extension :
            ehdr, epayload = self.extensionPacket

            print ehdr[0:2]

            packet.append( ehdr[0:2] )  # 2 bytes
            packet.append( struct.pack(">H", len(epayload)) )
            packet.append( epayload )
        
        packet.append(bytes(payload))

        packet=''.join(packet)              # combine packages

        return packet

    """
        setExtension(self,packet):
    """
    def setExtension(self,packet):
        self.extensionPacket = packet


    """
        getData
        This Function should retun important data of RTP Packet. 
    """
    def getData(self,packet):
        e = struct.unpack(">BBHII",packet[:12])
        
        if (e[0]>>6) != 2:       # check version is 2
            return None
        
        # ignore padding bit atm
        
        hasPadding   = e[0] & 0x20
        hasExtension = e[0] & 0x10
        numCSRCs     = e[0] & 0x0f
        hasMarker    = e[1] & 0x80
        payloadType  = e[1] & 0x7f
        seqnum       = e[2]
        timestamp    = e[3]
        ssrc         = e[4]
        
        i=12
        if numCSRCs:
            csrcs = struct.unpack(">"+str(numCSRCs)+"I", packet[i:i+4]) # remove i:i+4*crcs
            i=i+4*numCSRCs
        else:
            csrcs = []
            
        if hasExtension:
            ehdr, length = struct(">2sH",packet[i:i+4])
            epayload = packet[i+4:i+4+length]
            extension = (ehdr,epayload)
            i=i+4+length
        else:
            extension = None
        
        # now work out how much padding needs stripping, if at all
        end = len(packet)
        if hasPadding:
            amount = ord(packet[-1])
            end = end - amount
            
        payload = packet[i:end]

        return ( seqnum,
                 { 'payloadtype' : payloadType,
                   'payload'     : payload,
                   'timestamp'   : timestamp,
                   'ssrc'        : ssrc,
                   'extension'   : extension,
                   'csrcs'       : csrcs,
                   'marker'      : hasMarker,
                 }
               )

    """
        getPayloadInfos(self,pt):
    """
    def getPayloadInfos(self,pt):

        # 100
        if pt == 100:
            return {
                'format'    : 16,
                'channels'  : 1,
                'rate'      : 44100,
                'output'    : True,
            }



    """
        tailTime
        This Function should tail the time. From 64bit to 32bit. Last one and first seven.
        Resolution ist up to one Mikrosecond
        767466348
          |||||||
          s||||||
           mmm|||
              uuu
    """
    def tailTime(self, tn, latenz):

        tn = tn % 1000
        tn = int(tn * 1000000)
        tn +=(latenz*1000)

        return tn