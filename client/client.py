import socket 
import struct
import getch
UDPPORT = 13117

class Server:
    def __init__(self, addr, port):
        self.addr = addr
        self.port = port 
    
    
def gameMode(clientSocketTCP):
    #get the q and give an a 
    msgQuestion = clientSocketTCP.recv(2048)
    msgQuestion = msgQuestion.decode(encoding = 'utf-8', errors='ignore')
    print(msgQuestion)
    answer = getch.getch()
    answer = answer.encode(encoding= 'utf-8')
    clientSocketTCP.send(answer)
    msgSummery = clientSocketTCP.recv(2048)
    msgSummery = msgSummery.decode(encoding = 'utf-8', errors='ignore')
    if len(msgSummery) == 0:
        print("Server disconnected, listening for offer requests...")
    else:
        print(msgSummery)
    
def tcpConn(server):
    #exstablish tcp connection and move to game mode
    clientSocketTCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    with clientSocketTCP:
        try:
            clientSocketTCP.connect((server.addr , server.port))
            clientSocketTCP.sendall(b'teamTitans\n')
            gameMode(clientSocketTCP)          
        except Exception as error:
            print(error)
            return
        
def listenUDP():  
  # get hostName and hostAdress and move it to tcpConn
    clientSocketUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    with clientSocketUDP:
        clientSocketUDP.bind(("", UDPPORT))
        print("Client started, listening for offer requests...")
        while True:
            modifiedMessage, serverAddress = clientSocketUDP.recvfrom(2048)
            print("Received offer from", serverAddress[0], "attempting to connect...")
            try:
                magicCookie , messageType, ServerPort = struct.unpack('IbH', modifiedMessage)
                if hex(magicCookie) == '0xabcddcba' and hex(messageType) == '0x2':
                    server = Server(serverAddress[0], ServerPort)
                    tcpConn(server)  
                    print("ended")
            except:
                pass  
    
def main():
    listenUDP()


if __name__ == '__main__':
    main()