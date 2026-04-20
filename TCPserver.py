import json
import time
from socket import *
from threading import Thread

serverPort = 12001
serverName = "127.0.0.1"   # use localhost while testing alone
# serverName = "172.27.30.206"  # eduroam IP address but doesn't work according to video
# serverName = "" # empty string means server will listen on all available interfaces
# serverName = "" # hotspot IP address

serverSocket = socket(AF_INET, SOCK_STREAM)   # creating server-side socket
serverSocket.bind((serverName, serverPort))   # bind socket with IP and port
serverSocket.listen(1)                        # this line means server listens for the TCP connection req
print("The server is ready to receive")

clientDict = {}   # store connected clients as dictionary mapping usernames to sockets


def broadcast(message, senderSocket):
    for username, clientSocket in list(clientDict.items()):     # iterate through all connected clients
        if clientSocket != senderSocket:    # send message to all clients except the sender
            try:        # if the client is still connected, send the message
                clientSocket.send(message)
            except:     # if message sending fails, close the socket and remove it from the list
                clientSocket.close()
                if username in clientDict:
                    del clientDict[username]

def privateMessage(message, destinationSocket):
    # PRAJ TODO
    try:        
        destinationSocket.send(message)
    except:     
        pass


def clientHandler(connectionSocket, addr):
    # Username registration immediately upon connection
    try:
        username = connectionSocket.recv(1024).decode()
        clientDict[username] = connectionSocket
    except:
        connectionSocket.close()
        return

    # wait for messages from the client
    while True:
        try:
            sentence = connectionSocket.recv(4096)
            if not sentence: # if recv returns an empty byte string client has disconnected
                break
            print("Message received:", sentence.decode())
            
            try:
                # Handle Feature 3 JSON Application-Layer
                data = json.loads(sentence.decode())
                target = data.get("target", "ALL")
                
                if target == "ALL":
                    broadcast(sentence, connectionSocket)
                else:
                    if target in clientDict:
                        targetSocket = clientDict[target]
                        privateMessage(sentence, targetSocket)
                    else:
                        errorMsg = f"Error: Target user @{target} does not exist."
                        error_data = {
                            "sequence_number": 0,
                            "timestamp": time.time(),
                            "sender_username": "Server",
                            "target": username,
                            "payload": errorMsg
                        }
                        connectionSocket.send(json.dumps(error_data).encode())
                continue
            except json.JSONDecodeError:
                # Fallback to the original plain string behavior
                decodeSentence = sentence.decode()
                sentSentence = str(addr[1]) + ": " + sentence.decode()  # prepend client's port number to the message
                if decodeSentence[0] == "@":
                    # PRAJ TODO
                    # extract the socket from message and send to the socket
                    parts = decodeSentence.split(" ", 1)
                    targetUsername = parts[0][1:] # extract username without @
                    if targetUsername in clientDict:
                        targetSocket = clientDict[targetUsername]
                        privateMessage(sentSentence.encode(), targetSocket)
                    else:
                        errorMsg = f"Error: Target user @{targetUsername} does not exist."
                        connectionSocket.send(errorMsg.encode())
                    continue
                else: # no @ means user wanted to broadcast the message to all clients
                    broadcast(sentSentence.encode(), connectionSocket)
        except:
            break

    print("Client disconnected:", addr)
    if username in clientDict:  
        del clientDict[username]
    connectionSocket.close()


while True:
    # accept a new client connection 
    connectionSocket, addr = serverSocket.accept()
    
    # start a new client handler thread for each new connection
    clientThread = Thread(target=clientHandler, args=(connectionSocket, addr))
    clientThread.start()