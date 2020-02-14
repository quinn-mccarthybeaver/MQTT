import queue, selectors, socket, packets, threading

class SessionHandler:

    def __init__(self, sock, subq, pubq, outq):
        self.subq = subq
        self.pubq = pubq
        self.outq = outq
        self.timers = {}
        self.DEFAULT_TIMEOUT = 10 # in seconds
        self.live = True
        self.selector = selectors.DefaultSelector()
        self.selector.register(sock,
                               selectors.EVENT_READ,
                               self.socketread)
        self.handlesession(sock)
        
    def handlesession(self, sock):
        while self.live:
            if not self.outq.empty():
                self.selector.modify(sock, selectors.EVENT_WRITE, self.sendmessage)
            events = self.selector.select(-1)
            for key, _ in events:
                # callback is the afore-given function
                # fileobj, in this case, will always be a socket
                callback = key.data
                callback(key.fileobj)
                
    def socketread(self, sock):
        rawbytes = sock.recv(1024)
        if rawbytes:

            atLeastOnePacket = packets.decodepackets(rawbytes)
            for packet in atLeastOnePacket:
                # so python doesn't have a switch statement...
                if packet.messagenumber == 1: # connect
                    self.outq.put((packet.getCONNACK(), packet.QoS))
                elif packet.messagenumber == 3: # publish
                    msg = packet.getPUBLISH()
                    self.pubq.put((packet.topicname, msg, packet.retain))
                    if packet.QoS == 1:
                        self.outq.put((packet.getPUBACK(), 1))
                elif packet.messagenumber == 4: # PUBACK
                    if packet.messageid in self.timers:
                        self.timers[packet.messageid].cancel()
                elif packet.messagenumber == 8: # subscribe
                    for tn in packet.topicnames:
                        name, qos = tn
                        self.subq.put((True, (name, qos)))
                        self.outq.put((packet.getSUBACK(), qos))
                elif packet.messagenumber == 10: # unsubscribe
                    for name in packet.topicnames:
                        self.subq.put((False, (name, 0)))
                    self.outq.put((packet.getUNSUBACK(), 1))
                elif packet.messagenumber == 12: # PINGREQ
                    self.outq.put((packet.getPINGRESP(), 0))
                elif packet.messagenumber == 14: # DISCONNECT
                    self.shutdown(sock)
                    
        else:
            self.shutdown(sock)
            
    def sendmessage(self, sock):
        msg, qos = self.outq.get()
        if (msg[0] >> 4) == 3 and (not msg[0] & 2) and qos == 1:
            msg, msgID = packets.quality(msg)
            t = threading.Timer(self.DEFAULT_TIMEOUT, self.resendpublish, args=(msg,))
            self.timers[msgID] = t
            t.start()        
        sock.send(msg)
        self.selector.modify(sock, selectors.EVENT_READ, self.socketread)

    def resendpublish(self, msg):
        msg = packets.makedup(msg)
        self.outq.put((msg, 1))        

    def shutdown(self, sock):
        sock.close()
        self.live = False
