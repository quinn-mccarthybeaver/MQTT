import queue, selectors, packets

def spinup(q):
    handler = Handler()

    while True:
        if not q.empty():
            # sends new queues out to clients, put them in mailboxes
            # (subbox, pubbox, outbox)
            handler.mailboxes.append(q.get())
        for sub, pub, out in handler.mailboxes: # if there's mail, update state
            if not sub.empty(): # someone has a subscription
                subing, subscription = sub.get()
                if subing:
                    handler.subscribe(subscription, out)
                else:
                    handler.unsubscribe(subscription, out)
            if not pub.empty(): # someone has a publish
                topic, message, retain = pub.get()
                handler.publish(topic, message, retain)

class Handler:
    def __init__(self):

        # subbox receives subscriptions from clients
        # pubbox receives publishes
        # outbox is how we send publish messages to a client
        # (subbox, pubbox, outbox)
        self.mailboxes = []

        self.subscribers = SubTree()

    def publish(self, pubtopic, message, retain):
        self.subscribers.publish(pubtopic, message, retain)

    def subscribe(self, subscription, outbox):
        topic, qos = subscription
        self.subscribers.addsub(topic, outbox, qos)
        
    def unsubscribe(self, subscription, outbox):
        topic, _ = subscription
        self.subscribers.unsub(topic, outbox)

class SubTree:

    def __init__(self):
        # SubTrees: {topicLevel:SubTree}, [Subscribers]
        
        #[SubNodes]
        self.subtrees = {}
        self.subs = []

        # Topic:msg
        # with new structure this needs to change to be seperate
        self.retained = {}

    # updated
    # still needs retention update
    # walks down topic hierarchy, adding subtrees as needed. the top
    # level subtree will always be empty
    def addsub(self, topic, outbox, qos):
        topicLevels = topic.split("/")
        target = self
        for lvl in topicLevels:
            if lvl in target.subtrees:
                target = target.subtrees[lvl]
            else:
                toadd = SubTree()
                target.subtrees[lvl] = toadd
                target = toadd

        target.subs.append((outbox, qos))
        
    def unsub(self, topic, outbox):
        topic = topic.split("/")
        target = self
        for lvl in topic:
            if lvl == "+":
                for subtree in target.subtrees:
                    subtree.wildcardunsub(outbox)
                return
            elif lvl == "#":
                target.wildcardunsub(outbox)
                return
            else:
                if lvl in target.subtree:
                    target = target.subtree[lvl]
                else:
                    return

        for outtarget, qostarget in target.subs:
            if outtarget == outbox:
                target.subs.remove((outbox, qos))

    def wildcardunsub(self, outbox):
        for outtarget, qostarget in target.subs:
            if outtarget == outbox:
                target.subs.remove((outbox, qos))

        for subtree in target.subtrees:
            subtree.wildcardunsub(outbox)

    def publish(self, topic, msg, retain):
        if retain:
            print("retained msg, not implemented yet")
        topic = topic.split("/")
        target = self
        for lvl in topic:
            if lvl == "+":
                for subtree in target.subtrees:
                    subtree.wildcardpublish(msg, retain)
                return
            elif lvl == "#":
                target.wildcardpublish(msg, retain)
                return
            else:
                if lvl in target.subtree:
                    target = target.subtree[lvl]
                else:
                    return

        for out, qos in target.subs:
            out.put((msg, qos))

    # save this, might be useful when reimplementing retain
    def oldpublish(self, topic, msg, retain):
        if retain:
            self.retained[topic] = packets.makeretain(msg)
        topic = topic.split("/")
        for node in self.subnodes:
            if node.topic == topic[0] or node.topic == "+":
                node.publish(topic[1:], msg)
            elif node.topic == "#":
                node.publish([], msg)

    def match(topic1, topic2):
        if len(topic1) >= len(topic2):
            topiclong = topic1.split("/")
            topicshort = topic2.split("/")
        else:
            topiclong = topic2.split("/")
            topicshort = topic1.split("/")
        i = 0
        for topic in topicshort:
            if topic == "#" or topiclong[i] == "#":
                return True
            elif topic == "+" or topiclong[i] == "+":
                i += 1
                continue
            elif topic == topiclong[i]:
                i += 1
                continue
            else:
                return False
        return True

class SubNode:

    def __init__(self, topic):
        # [(outbox, qos)]
        self.subscribers = []

        # [SubNode]
        self.subtopics = []

        # String
        self.topic = topic

    def unsub(self, topic, outbox):
        if topic == []:
            for sub in self.subscribers:
                if sub[0] == outbox:
                    self.subscribers.remove((outbox, sub[1]))
        elif topic[0] == "#":
            for sub in self.subscribers:
                if sub[0] == outbox:
                    self.subscribers.remove((outbox, sub[1]))
            for node in self.subtopics:
                node.unsub(topic, outbox)
        else:
            for node in self.subtopics:
                if (node.topic == topic[0] or topic[0] == "+") and node.topic != "#":
                    node.unsub(topic[1:], outbox)

    def addsub(self, topic, outbox, qos):
        if topic == []:
            self.subscribers.append((outbox, qos))
        else:
            if self.subtopics == []:
                self.subtopics.append(SubNode(topic[0]))
            for node in self.subtopics:
                if node.topic == topic[0]:
                    node.addsub(topic[1:], outbox, qos)
                    break
            else:
                toappend = SubNode(topic[0])
                toappend.addsub(topic[1:], outbox, qos)
                self.subtopics.append(toappend)
        
    def publish(self, topic, msg):
        if topic == []:
            for sub in self.subscribers:
                outbox, qos = sub
                outbox.put((msg, qos))
        else:
            for node in self.subtopics:
                if topic[0] == node.topic or node.topic == "+":
                    node.publish(topic[1:], msg)
                elif node.topic == "#":
                    node.publish([], msg)
