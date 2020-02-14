## COS 460/540 - Computer Networks
# Project : MQTT Server

# Quinn McCarthy Beaver

This project is written in Python3 on Arch Linux

## How to compile

Python doesn't really have a compile step, see run instructions.

## How to run

make sure you're using the latest version of Python (3.8)
to compile/run program run the command :

python3 MQTT.py $HOST $PORT

$HOST should be a valid IPv4 address and $PORT should be an available
port. 127.0.0.1 and 1883 are convenient choices because Mosquitto
clients will automatically connect to there. Any port under 1024 may
need to be run as root/sudo.

To exit hit CTRL-C until it stops moving.

## My experience with this project

I would say the most challenging programming assignment I've had to
date. I'm glad I chose python as my language, even though I have more
experience with java overall I would have been learning many new
things (threading, multi-user/consumer queues, etc.) for the first
time anyway, and python has some really nice APIs for everything.

There were several times where I implemented something using my best
guess, only to go back and read the docs and realize that yes, they
did actually specify what they wanted, and no, I didn't implement it
the right way. Overall there's a lot of cleaning up to do of the code,
but I'm satisfied with how it runs, I believe it's to spec.

My favorite part is that this interfaces with real tools like
mosquitto. I don't feel like I'm just writing code just for the
homework, This is actually a tool I could put in a portfolio once it's
fully implemented.
