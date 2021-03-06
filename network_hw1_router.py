import socket
import select
import sys
import time
from random import *
import matplotlib.pyplot as plt
HEADER_LENGTH = 10

IP = "127.0.0.1"
PORT = 1234

###I learned how to do python sockets and used the following code links
#https://pythonprogramming.net/server-chatroom-sockets-tutorial-python-3/ 
#https://pythonprogramming.net/client-chatroom-sockets-tutorial-python-3/?completed=/server-chatroom-sockets-tutorial-python-3/


# Create a socket
# socket.AF_INET - address family, IPv4, some otehr possible are AF_INET6, AF_BLUETOOTH, AF_UNIX
# socket.SOCK_STREAM - TCP, conection-based, socket.SOCK_DGRAM - UDP, connectionless, datagrams, socket.SOCK_RAW - raw IP packets
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# SO_ - socket option
# SOL_ - socket option level
# Sets REUSEADDR (as a socket option) to 1 on socket
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Bind, so server informs operating system that it's going to use given IP and port
# For a server using 0.0.0.0 means to listen on all available interfaces, useful to connect locally to 127.0.0.1 and remotely to LAN interface IP
server_socket.bind((IP, PORT))

# This makes server listen to new connections
server_socket.listen()

# List of sockets for select.select()
sockets_list = [server_socket]

# List of connected clients - socket as a key, user header and name as data
clients = {}

print(f'Listening for connections on {IP}:{PORT}...')

# Handles message receiving
messageCounter = {}
packets = [ 150, 250, 450, 650, 850, 1000]

for packet in packets:
    messageCounter[packet] = 0

def receive_message(client_socket):

    try:

        # Receive our "header" containing message length, it's size is defined and constant
        message_header = client_socket.recv(HEADER_LENGTH)

        # If we received no data, client gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
        if not len(message_header):
            return False

        # Convert header to int value
        message_length = int(message_header.decode('utf-8').strip())

        # Return an object of message header and message data
        return {'header': message_header, 'data': client_socket.recv(message_length)}

    except:
        return False
global receivedpacket
receivedpacket = False
global waitCounter
waitCounter = 0
global timestart
global timeend
timestart = None
timeend = None
global throughput
throughput = 0
while True:
    read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)
    

    # Iterate over notified sockets
    for notified_socket in read_sockets:

        # If notified socket is a server socket - new connection, accept it
        if notified_socket == server_socket:

            # Accept new connection
            # That gives us new socket - client socket, connected to this given client only, it's unique for that client
            # The other returned object is ip/port set
            client_socket, client_address = server_socket.accept()

            # Client should send his name right away, receive it
            user = receive_message(client_socket)

            # If False - client disconnected before he sent his name
            if user is False:
                print('user died')
                sys.exit('user died')

            # Add accepted socket to select.select() list
            sockets_list.append(client_socket)

            # Also save username and username header
            clients[client_socket] = user

            print('Accepted new connection from {}:{}, username: {}'.format(*client_address, user['data'].decode('utf-8')))

        # Else existing socket is sending a message
        else:
            
            # Receive message
            message = receive_message(notified_socket)
            
            if waitCounter > 5000 and receivedpacket:
                x = []
                y = []
                for key in messageCounter:
                    x.append(key)
                    y.append(messageCounter[key])
                    print(key, ' required ', messageCounter[key],' attempts')
          
                colors = (0,0,0)
                # Plot
                plt.scatter(x, y, s=30, c='red', alpha=0.5)
                plt.title('Networking homework 1 part b')
                plt.suptitle('Throughput was ' + str(int(throughput))+ 'bytes/sec')
                plt.xlabel('number of packets')
                plt.ylabel('packets sent')
                plt.savefig('sentpackets.png')
                plt.close()
                sys.exit('all packets sent')

            if message == False:
                waitCounter+=1
                continue
                #print('user may have died')
                #sys.exit('user mah have died')
            waitCounter = 0
            
            print(type(message['data']),message)
            assert isinstance(message['data'], bytes)

            # Get user by notified socket, so we will know who sent the message
            user = clients[notified_socket]

            
            print(f'Received message from {user["data"].decode("utf-8")}: {message["data"].decode("utf-8")}')

            for key in messageCounter:
                if str(key) in message['data'].decode('utf-8') and 'nak' not in message['data'].decode('utf-8'):
                    messageCounter[key]+=1
            now = time.time()
            if timestart == None:
                if '1000' in message['data'].decode('utf-8') :
                    timestart = time.time()
            elif timeend == None and now-timestart > 2:
                brec = messageCounter[1000]*int(message['header'].decode('utf-8').strip())
                throughput = brec/(now-timestart)
                timeend= now
                
            receivedpacket = True
            un = user["data"].decode("utf-8")
            x = 7
            if random() < .1*x: # drop packets 
                break
            # Iterate over connected clients and broadcast message
            for client_socket in clients:

                # But don't sent it to sender
                if client_socket != notified_socket:
                    if 'nak' in message['data'].decode('utf-8'):
                        print ('nak',user['header'].decode('utf-8'))
                    # Send user and message (both with their headers)
                    # We are reusing here message header sent by sender, and saved username header send by user when he connected
                    client_socket.send(user['header'] + user['data'] + message['header'] + message['data'])

