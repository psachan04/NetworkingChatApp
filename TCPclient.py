import json
import time
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
    expected_seq = {}
    while True:
        try:
            sentence = clientSocket.recv(4096)
            if not sentence:
                break
                
            try:
                # Handle Feature 3 JSON Application-Layer
                data = json.loads(sentence.decode())
                sender = data.get("sender_username", "Unknown")
                seq = data.get("sequence_number", 0)
                ts = data.get("timestamp", 0)
                payload = data.get("payload", "")
                
                # Check latency and verify message ordering
                latency = (time.time() - ts) * 1000
                expected = expected_seq.get(sender, 1)
                order_status = "In Order" if seq == expected else f"Out of Order"
                if sender != "Server":
                    expected_seq[sender] = max(expected, seq) + 1
                
                metric_str = f"[{sender} | Latency: {latency:.2f} ms | Seq: {seq} - {order_status}]"
                print("\nMessage received from", f"{metric_str} {payload}") # print received message on new line
                print("Input message: ", flush=True, end="") # print input prompt again after receiving a message
            except json.JSONDecodeError:
                # Original plain string processing fallback
                print("\nMessage received from", sentence.decode()) # print received message on new line
                print("Input message: ", flush=True, end="") # print input prompt again after receiving a message
        except:
            break


receiveThread = Thread(target=receiveMessages, daemon=True)
receiveThread.start()

sequence_number = 1
while True:
    sentence = input("Input message: ")
    if sentence.lower() == "exit": # client can gracefully exit by typing "exit"    
        break
        
    target = "ALL"
    message_payload = sentence
    if sentence.startswith("@"):
        parts = sentence.split(" ", 1)
        target = parts[0][1:]
        message_payload = parts[1] if len(parts) > 1 else ""

    # JSON protocol wrapper for Feature 3
    message_data = {
        "sequence_number": sequence_number,
        "timestamp": time.time(),
        "sender_username": username,
        "target": target,
        "payload": message_payload
    }
    sequence_number += 1
    
    clientSocket.send(json.dumps(message_data).encode())

clientSocket.close()