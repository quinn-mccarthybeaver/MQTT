import queue, selectors, packets


def spinup(q):
    handler = Handler()

    while True:
        if not q.empty():
            # sends new queues out to clients, put them in mailboxes
            # (subbox, pubbox, outbox)
            handler.mailboxes.append(q.get())
        for sub, pub, out in handler.mailboxes:  # if there's mail, update state
            if not sub.empty():  # someone has a subscription
                subing, subscription = sub.get()
                if subing:
                    handler.subscribe(subscription, out)
                else:
                    handler.unsubscribe(subscription, out)
            if not pub.empty():  # someone has a publish
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

        self.subtrees = {}
        self.subs = []

        # Topic:msg
        # with new structure this needs to change to be seperate
        self.retained = None

    # updated
    # still needs retained messages update
    # walks down topic hierarchy, adding subtrees as needed. the top
    # level subtree will always be empty
    # Maybe some kind of topic verifying?
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

        if target.retained != None:
            outbox.put((target.retained, qos))

    # first walks down the tree until the right topic level is found
    # next searches the subscribers array for the outbox of the
    # subscriber in question and removes them
    def unsub(self, topic, outbox):
        topic = topic.split("/")
        target = self
        for lvl in topic:
            if lvl in target.subtree:
                target = target.subtree[lvl]
            else:
                # the topic isn't in the tree, so do nothing
                return

        # somehow clean up tree here?
        # send kill msg to client handler when we remove?
        for outtarget, qostarget in target.subs:
            if outtarget == outbox:
                target.subs.remove((outbox, qos))
                return

    # actually the only place that wildcards need to be handled. We
    # can't publish to a wildcard, but when a wildcard is found while
    # traversing the tree we need to treat that as a match (switched
    # to a recursvie approach)
    def publish(self, topic, msg, retain):
        topic = topic.split("/")
        self.publishrec(topic, msg, retain)

    def publishrec(self, topic, msg, retain):
        if topic == []:
            for outbox, qos in self.subs:
                outbox.put((msg, qos))
            if retain:
                self.retained = msg
                print("retained")
        else:
            currentlvl = topic[0]
            topic = topic[1:]
            if "+" in self.subtrees:
                self.subtrees["+"].publishrec([], msg, False)
            if "#" in self.subtrees:
                self.subtrees["#"].publishrec([], msg, False)
            if currentlvl in self.subtrees:
                self.subtrees[currentlvl].publishrec(topic, msg, retain)
