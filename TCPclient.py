from socket import *
from threading import Thread

serverPort = 12001
serverName = "127.0.0.1"   # use localhost while testing alone
# serverName = "172.27.30.206"  # eduroam IP address but doesn't work according to video
# serverName = "" # empty string means server will listen on all available interfaces
# serverName = "" # hotspot IP address

clientSocket = socket(AF_INET, SOCK_STREAM)   # creates client-side TCP socket
clientSocket.connect((serverName, serverPort)) # initiate TCP connection to the server. after this line is executed, three way tcp connection is established

# Prompt for username immediately upon connection
username = input("Enter your username: ")
clientSocket.send(username.encode())

print("Connected to server")


def receiveMessages():
    while True:
        try:
            sentence = clientSocket.recv(1024)
            if not sentence:
                break
            print("\nMessage received from", sentence.decode()) # print received message on new line
            print("Input message: ", flush=True, end="") # print input prompt again after receiving a message
        except:
            break


receiveThread = Thread(target=receiveMessages, daemon=True)
receiveThread.start()

while True:
    sentence = input("Input message: ")
    if sentence.lower() == "exit": # client can gracefully exit by typing "exit"    
        break
    clientSocket.send(sentence.encode())

clientSocket.close()