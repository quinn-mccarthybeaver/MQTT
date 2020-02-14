import random

def decodepackets(rawbytes):
    toReturn = []
    while rawbytes:
        remaininglen = rawbytes[1]
        toReturn.append(DecodedPacket(rawbytes[0:2+remaininglen]))
        rawbytes = rawbytes[2+remaininglen:]
    return toReturn

def quality(rawbytes):
    firstByte = rawbytes[0] | 2
    messageid = random.randint(0,255).to_bytes(2, "big")
    offset = int.from_bytes(rawbytes[2:4], "big")
    length = len(rawbytes[2:4+offset] + messageid + rawbytes[4+offset:])
    return (firstByte.to_bytes(1, byteorder="big") + length.to_bytes(1, "big") + rawbytes[2:4+offset] + messageid + rawbytes[4+offset:], messageid)

def makedup(rawbytes):
    firstByte = rawbytes[0] | 4
    return firstByte.to_bytes(1, byteorder="big") + rawbytes[1:]

def makeretain(rawbytes):
    secondByte = rawbytes[1] | 1
    return rawbytes[0].to_bytes(1, byteorder="big") + secondByte.to_bytes(1, byteorder="big") + rawbytes[2:]

class DecodedPacket:

    def __init__(self, b):
        firstByte = b[0]
        secondByte = b[1]

        self.retain = firstByte & 1
        self.QoS = (firstByte >> 1) & 3
        self.DUP = (firstByte >> 3) & 1
        self.messagenumber = (firstByte >> 4)
        payload = b[2:]

        if self.messagenumber == 3: # publish
            self.publish(payload)
        elif self.messagenumber == 4:
            self.messageid = payload[0:2]
        elif self.messagenumber == 5:
            self.messagetype = "pubrec"
        elif self.messagenumber == 6:
            self.messagetype = "pubrel"
        elif self.messagenumber == 7:
            self.messagetype = "pubcomp"
        elif self.messagenumber == 8: # subscribe
            self.subscribe(payload)
        elif self.messagenumber == 9:
            self.messagetype = "suback"
        elif self.messagenumber == 10:
            self.unsubscribe(payload)
        elif self.messagenumber == 11:
            self.messagetype = "unsuback"
        elif self.messagenumber == 12:
            self.messagetype = "pingreq"
        elif self.messagenumber == 13:
            self.messagetype = "pingresp"
        elif self.messagenumber == 14:
            self.messagetype = "disconnect"



    def publish(self, payload):
        offset = int.from_bytes(payload[0:2], "big")
        self.topicname = payload[2:(offset+2)].decode("utf-8")
        if self.QoS > 0:
            self.messageid = payload[(offset+2):(offset+4)]
            self.msg = payload[(offset+4):]
        else:
            self.msg = payload[(offset+2):]

    def getPUBLISH(self):
        header = b'\x30'
        topiclength = len(self.topicname).to_bytes(2, byteorder='big')
        self.msg = topiclength + self.topicname.encode("utf-8") + self.msg
        msglength = len(self.msg).to_bytes(1, byteorder='big')
        return header + msglength + self.msg

    def unsubscribe(self, payload):
        self.messageid = payload[0:2]
        payload = payload[2:]
        self.topicnames = []
        while payload:
            length = int.from_bytes(payload[0:2], "big")
            self.topicnames.append(payload[2:2+length].decode("utf-8"))
            payload = payload[2+length:]

    def subscribe(self, payload):
        self.messageid = payload[0:2]
        payload = payload[2:]
        self.topicnames = []
        while payload:
            length = int.from_bytes(payload[0:2], "big")
            name = payload[2:2+length].decode("utf-8")
            desiredqos = int.from_bytes(payload[2+length:3+length], "big") & 3
            payload = payload[3+length:]
            self.topicnames.append((name, desiredqos))

    def getSUBACK(self):
        header = b'\x90'
        body = self.messageid
        for n in self.topicnames:
            body += n[1].to_bytes(1, byteorder="big")
        remaininglen = len(body).to_bytes(1, byteorder='big')
        return header + remaininglen + body

    def getUNSUBACK(self):
        return b'\xb0\x02' + self.messageid

    def getPUBACK(self):
        return b'\x40\x02' + self.messageid

    def getCONNACK(self):
        return b'\x20\x02\x00\x00'

    def getPINGRESP(self):
        return b'\xd0\x00'
