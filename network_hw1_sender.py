import socket
import select
import errno
import sys
import time
import uuid
HEADER_LENGTH = 10

IP = "127.0.0.1"
PORT = 1234
my_username = "sender"

###
###I learned how to do python sockets and used the following code links
#https://pythonprogramming.net/server-chatroom-sockets-tutorial-python-3/ 
#https://pythonprogramming.net/client-chatroom-sockets-tutorial-python-3/?completed=/server-chatroom-sockets-tutorial-python-3/

# Create a socket
# socket.AF_INET - address family, IPv4, some otehr possible are AF_INET6, AF_BLUETOOTH, AF_UNIX
# socket.SOCK_STREAM - TCP, conection-based, socket.SOCK_DGRAM - UDP, connectionless, datagrams, socket.SOCK_RAW - raw IP packets
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to a given ip and port
client_socket.connect((IP, PORT))

# Set connection to non-blocking state, so .recv() call won;t block, just return some exception we'll handle
client_socket.setblocking(False)

# Prepare username and header and send them
# We need to encode username to bytes, then count number of bytes and prepare header of fixed size, that we encode to bytes as well
username = my_username.encode('utf-8')
username_header = f"{len(username):<{HEADER_LENGTH}}".encode('utf-8')
client_socket.send(username_header + username)

packets = [ 150, 250, 450, 650, 850, 1000]
#packets = [150]
global respnak
respnak = 0

global conts
conts = 0
lastReceivedNak = None

def receive_naks(messageDict):
    global respnak
    while True:
        print('1')
        # Receive our "header" containing username length, it's size is defined and constant
        username_header = client_socket.recv(HEADER_LENGTH)
        print('2')
        
        # Convert header to int value
        username_length = int(username_header.decode('utf-8').strip())
        print('3')
        
        # Receive and decode username
        username = client_socket.recv(username_length).decode('utf-8')
        print('4')
        
        if username != 'receiver':
            print('messages being received from unknown user', username)
            sys.exit()
        print('5')
        
        # Now do the same for message (as we received username, we received whole message, there's no need to check if it has any length)
        message_header = client_socket.recv(HEADER_LENGTH)
        message_length = int(message_header.decode('utf-8').strip())
        message = client_socket.recv(message_length).decode('utf-8')
        m = message.split()
        lastReceivedNak = time.time()
        print('6')
        
        assert len(m) == 3
        uid = m[2]
        print (m)
        if 'nak' in m:
            ind =  m[1]
            #ind = ind -1 # adjust for 0 indicies
            #assert isinstance(ind,int)
            rm = None
            print('ind',type(ind), ind)
                
            for message in messageDict[uid]: #should be message header + message
                rind = message.decode('utf-8').split()[2]#header hasn't been removed so add 1 to normal indexing
                if rind == ind:
                    rm = message
                    break
            if rm == None:
                print ('rm is none')
            assert rm != None
            if 'nak' in message.decode('utf-8'):
                print('sending a nak, error')
                sys.exit()
            print ('receivnaksresponse',rm)
            client_socket.send(rm)
            print ('after send')
            print("responsenaks",respnak)
            respnak+=1
            conts = 0
            #if respnak >= 100:
            #    time.sleep(5)
            #    sys.exit('testing')
            print('returning lost packet')
        else:
            # Print message
            print(f'{username} > {message}')

messageDict = {}
lastUid = ""
startime = time.time()

for packet in packets:
    uid = uuid.uuid1()
    uid = str(uid)
    assert lastUid!=uid
    #uid = uid.encode('utf-8')
    messageDict[uid] = []
    for packet_number in range(1,packet+1,1):
        #time.sleep(.01)

        # Wait for user to input a message
        message = str(packet)+'\n'+str(packet_number)+'\n'+uid
        
        # Encode message to bytes, prepare header and convert to bytes, like for username above, then send
        message = message.encode('utf-8')
        message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
        message = message_header + message
        
        messageDict[uid].append(message)

        try:
            # Now we want to loop over received messages (there might be more than one) and print them
            if(not isinstance(message,bytes)):
                print (isinstance(message,bytes))
            client_socket.send(message)
            #time.sleep(.01)
            receive_naks(messageDict)
                        

        except IOError as e:
            # This is normal on non blocking connections - when there are no incoming data error is going to be raised
            # Some operating systems will indicate that using AGAIN, and some using WOULDBLOCK error code
            # We are going to check for both - if one of them - that's expected, means no incoming data, continue as normal
            # If we got different error code - something happened
            if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                print('Reading error: {}'.format(str(e)))
            
        
            # We just did not receive anything
            continue
            time.sleep(.0001)
            
        except Exception as e:
            # Any other exception - something happened, exit
            print('Reading error: '.format(str(e)))
            time.sleep(.0001)


endtime = time.time()

print('entering extra while loop\n\n\n')
while True:
    try:
        # Now we want to loop over received messages (there might be more than one) and print them
        if conts > 50000:
            totalPackets = 0
            for x in packets:
                totalPackets+=x
            print('maximum throughput (ignoring dropped packets) was ', totalPackets*45.0/(endtime-startime),' bytes per second')
            sys.exit('successfully finished sending all packets over noisy router (.7 probability of failure)')
        receive_naks(messageDict)
        
                
    except IOError as e:
        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
            print('Reading error: {}'.format(str(e)))
        # We just did not receive anything
        time.sleep(.0001)
        conts+=1
        continue

    except Exception as e:
        # Any other exception - something happened, exit
        conts+=1
        continue
