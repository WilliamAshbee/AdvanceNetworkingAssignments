import socket
import select
import errno
import sys
import time
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
i =0

receivedDecodedMessages = {}
missingMessages = {}
messageKeys = []
        
while True:
    message = False
    # If message is not empty - send it
    if message:

        # Encode message to bytes, prepare header and convert to bytes, like for username above, then send
        message = message.encode('utf-8')
        client_socket.send(message_header + message)

    try:
        # Now we want to loop over received messages (there might be more than one) and print them
        while True:
            i+=1
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
            uid = messageList[2]
            pnum = int(messageList[1])
            if i % 10 ==0:#this will go away completely or be replaced with a check
                nak = 'nak\n'+str(messageList[1])+'\n'+str(messageList[2])
                nak = nak.encode('utf-8')
                message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
                client_socket.send(message_header + nak)
                if uid not in missingMessages:
                    missingMessages[uid] = []
                    missingMessages[uid].append(pnum)
                else:
                    missingMessages[uid].append(pnum)
            else:
                #store in received messages
                if uid in receivedDecodedMessages:
                    haveSaved = False
                    for el in receivedDecodedMessages[uid]:
                        m = el.split()
                        if int(m[1]) == pnum:
                             haveSaved = True
                             break
                    if not haveSaved:
                        receivedDecodedMessages[uid].append( message)
                    else:
                        print ('duplicate packet received',message)
                else:
                    receivedDecodedMessages[uid] = []
                    receivedDecodedMessages[uid].append(message)
                    
                if uid not in messageKeys:
                    messageKeys.append(uid)
                if uid in missingMessages:
                    print('uid in missing messages')
                    while pnum in missingMessages[uid]:
                        missingMessages[uid].remove(pnum)
                        print('removing missing message', uid, pnum)

            # Print message
            #print(f'{username} > {message}')
            print(missingMessages)

    except IOError as e:
        # This is normal on non blocking connections - when there are no incoming data error is going to be raised
        # Some operating systems will indicate that using AGAIN, and some using WOULDBLOCK error code
        # We are going to check for both - if one of them - that's expected, means no incoming data, continue as normal
        # If we got different error code - something happened
        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
            print('Reading error: {}'.format(str(e)))
        time.sleep(.01)
        # We just did not receive anything
        continue

    except Exception as e:
        # Any other exception - something happened, exit
        
        print('Reading error: '.format(str(e)))
