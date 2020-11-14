import threading, socket, sessionhandler, subhandler, queue, sys
# selectors

try:
    HOST = sys.argv[1]
    PORT = int(sys.argv[2])
except:
    print("improper arguments.")
    print(
        "First arg must be a valid IPv4 address, second arg must be a valid and available port number."
    )
    sys.exit(0)

listenSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listenSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
listenSocket.bind((HOST, PORT))

# this queue is how we send messages to the subscription handler thread
q = queue.SimpleQueue()
threading.Thread(target=subhandler.spinup, args=(q, )).start()

while True:
    listenSocket.listen()
    connsocket, addr = listenSocket.accept()

    # these queues are how the sessionhandler will communicate with
    # the subhandler:
    # subqueue: communicates subscriptions
    # pubqueue: communicates messages the client wants to publish
    # sendqueue: used to distribute published messages to everyone whos subscribed
    # sockqueue = queue.SimpleQueue()
    subqueue = queue.SimpleQueue()
    pubqueue = queue.SimpleQueue()
    sendqueue = queue.SimpleQueue()

    q.put((subqueue, pubqueue, sendqueue))
    threading.Thread(target=sessionhandler.SessionHandler,
                     args=(connsocket, subqueue, pubqueue, sendqueue)).start()
