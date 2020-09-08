import socket
import select
import errno
import sys
import time
HEADER_LENGTH = 10

IP = "127.0.0.1"
PORT = 1234
my_username = "sender"

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

def receive_naks(messages):
    while True:
        # Receive our "header" containing username length, it's size is defined and constant
        username_header = client_socket.recv(HEADER_LENGTH)

        # Convert header to int value
        username_length = int(username_header.decode('utf-8').strip())

        # Receive and decode username
        username = client_socket.recv(username_length).decode('utf-8')

        # Now do the same for message (as we received username, we received whole message, there's no need to check if it has any length)
        message_header = client_socket.recv(HEADER_LENGTH)
        message_length = int(message_header.decode('utf-8').strip())
        message = client_socket.recv(message_length).decode('utf-8')

        m = message.split()
        print('length m', len(m))
        assert len(m) == 2
        if 'nak' in m:
            try:
                ind = (int) (m[1])
                assert isinstance(ind,int)
                message = messages[ind] #should be message header + message
                assert isinstance(message,bytes)
                print ('receivnaksresponse',message)
                client_socket.send(message)
                print('returning lost packet')

            except Exception as e: 
                print(e)
                print("exception triggered by following token", m[1])
        else:
            # Print message
            print(f'{username} > {message}')


for packet in packets:
    messages = []

    for packet_number in range(packet):
        time.sleep(.01)

        # Wait for user to input a message
        message = str(packet)+'\n'+str(packet_number)
        messages.append(message)
    
        # Encode message to bytes, prepare header and convert to bytes, like for username above, then send
        message = message.encode('utf-8')
        message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
        try:
            # Now we want to loop over received messages (there might be more than one) and print them
            message = message_header + message
            assert isinstance(message,bytes) # TODO: remember to save the message number eventually
            messages.append(message)
            client_socket.send(message)
            receive_naks(messages)
            

        except IOError as e:
            # This is normal on non blocking connections - when there are no incoming data error is going to be raised
            # Some operating systems will indicate that using AGAIN, and some using WOULDBLOCK error code
            # We are going to check for both - if one of them - that's expected, means no incoming data, continue as normal
            # If we got different error code - something happened
            if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                print('Reading error: {}'.format(str(e)))
                
            # We just did not receive anything
            continue

        except Exception as e:
            # Any other exception - something happened, exit
            print('Reading error: '.format(str(e)))

while True:
    try:
        # Now we want to loop over received messages (there might be more than one) and print them
        receive_naks()
                
    except IOError as e:
        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
            print('Reading error: {}'.format(str(e)))
        # We just did not receive anything
        continue

    except Exception as e:
        # Any other exception - something happened, exit
        print('Reading error: '.format(str(e)))
