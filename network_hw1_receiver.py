import socket
import select
import errno
import sys
import time
import random
HEADER_LENGTH = 10

IP = "127.0.0.1"
PORT = 1234
my_username = "receiver"

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

receivedDecodedMessages = {}
messageKeys = []
missingMessages = {}
duplicateMessages = 0
global packets
packets = {}



def createMissingSet(key):
    print('create missing set')
    firstM = receivedDecodedMessages[key][0]
    msglength = (int)(firstM.split()[0])
    receivedSet= set()
    #max = -1
    if msglength > len(receivedDecodedMessages[key]):
        for rdm in receivedDecodedMessages[key]:
            temp = (int)(rdm.split()[1])
            #if temp > max:
            #    max = temp
            receivedSet.add(temp)
        maxSet = [x for x in range (1,msglength+1,1)]
        maxSet = (set) (maxSet)
        missingset = maxSet-receivedSet
        missingMessages[key] = missingset
        print('missing set', missingMessages[key])
        
def sendRequiredNaks():
    for key in missingMessages:
        if len(missingMessages[key]) > 0:
            print ('send naks')
            missingpacket = random.choice((list)(missingMessages[key]))
            print("missingpacket",missingpacket)
            nak = 'nak\n'+str(missingpacket)+'\n'+str(key) #nak\npacketnum\nuuid
            nak = nak.encode('utf-8')
            message_header = f"{len(nak):<{HEADER_LENGTH}}".encode('utf-8')#lenmessage
            print(nak)
            client_socket.send(message_header + nak)
            print(message_header+nak)
        
                
lastuuid = ""
global receivedMessage
receivedMessage = False
global contCount 
contCount = 0

while True:
    try:
        # Now we want to loop over received messages (there might be more than one) and print them
        while True:
            # Receive our "header" containing username length, it's size is defined and constant
            username_header = client_socket.recv(HEADER_LENGTH)

            # If we received no data, server gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
            if not len(username_header):
                print('Connection closed by the server')
                sys.exit()

            # Convert header to int value
            username_length = int(username_header.decode('utf-8').strip())

            # Receive and decode username
            username = client_socket.recv(username_length).decode('utf-8')
            if username != 'sender':
                print('shouldnt be receiving receiver packets')
                sys.exit()
            # Now do the same for message (as we received username, we received whole message, there's no need to check if it has any length)
            
            message_header = client_socket.recv(HEADER_LENGTH)
            message_length = int(message_header.decode('utf-8').strip())
            message = client_socket.recv(message_length).decode('utf-8')
            messageList = message.split()
            assert len(messageList) == 3
            length = int(messageList[0])
            uid = messageList[2]
            packets[uid] = length
            
            pnum = int(messageList[1])
            if uid in missingMessages:
                while (pnum in missingMessages[uid]):
                    missingMessages[uid].remove(pnum)
                    print('removing', uid, pnum)
                if pnum in missingMessages[uid]:
                    print('error is here')
                assert pnum not in missingMessages[uid]
                
            

            #store in received messages
            print(uid,pnum)
            if uid in receivedDecodedMessages:
                haveSaved = False
                for el in receivedDecodedMessages[uid]:
                    m = el.split()
                    if int(m[1]) == pnum:
                            print('duplicate',m)
                            haveSaved = True
                            break
                if not haveSaved:
                    print('saving')
                    receivedDecodedMessages[uid].append(message)
                else:
                    duplicateMessages+=1
                    print('duplicate packet received',message)
                    print('total duplicates',duplicateMessages)
            else:
                print('first uid')
                receivedDecodedMessages[uid] = []
                receivedDecodedMessages[uid].append(message)

            if uid not in messageKeys:
                receivedMessage = True
                if lastuuid != "":
                    createMissingSet(lastuuid)
                lastuuid = uid
                
                messageKeys.append(uid)

            sendRequiredNaks()

            if receivedMessage:
                contCount = 0
            # Print message
            #print(f'{username} > {message}')
            #print(missingMessages)

    except IOError as e:
        # This is normal on non blocking connections - when there are no incoming data error is going to be raised
        # Some operating systems will indicate that using AGAIN, and some using WOULDBLOCK error code
        # We are going to check for both - if one of them - that's expected, means no incoming data, continue as normal
        # If we got different error code - something happened
        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
            print('Reading error: {}'.format(str(e)))
        # We just did not receive anything
        if receivedMessage:
            contCount+=1
        else:
            time.sleep(.001)
            sendRequiredNaks()
        if contCount > 100000:
            receivedMessage = False
            contCount = 0
            createMissingSet(lastuuid)
        #print('continuing',contCount)
        
        
        printFinalResults = len(receivedDecodedMessages) == 6
        for key in receivedDecodedMessages:
            if len(receivedDecodedMessages[key]) != int(packets[key]):
                printFinalResults = False
                break
        if printFinalResults:
            print('all packets received')
            for key in receivedDecodedMessages:
                print("message uid ", key,  ' received all of its', packets[key], ' packets')
            time.sleep(2)
            sys.exit('exiting successfully')
        
        continue
        

    except Exception as e:
        # Any other exception - something happened, exit
        
        print('Reading error: '.format(str(e)))
