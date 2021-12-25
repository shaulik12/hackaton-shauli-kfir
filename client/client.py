import socket 
import struct
import msvcrt

UDPPORT = 13117

class Server:
    def __init__(self, addr, port):
        self.addr = addr
        self.port = port 
    
    
def gameMode(clientSocketTCP):
    #get the q and give an a 
    msgQuestion = clientSocketTCP.recv(2048)
    print(msgQuestion)
    answer = msvcrt.getch()
    clientSocketTCP.send(answer)
    while True:
        msgSummery = clientSocketTCP.recv(4096)
        if len(msgSummery) == 0:
            print("Server disconnected, listening for offer requests...")
            break
        else:
            print(msgSummery)
    
def tcpConn(server):
    #exstablish tcp connection and move to game mode
    clientSocketTCP = socket.socket(socket.AF_INET , socket.SOCK_DGRAM)
    with clientSocketTCP:
        try:
            clientSocketTCP.connect(server.addr , server.port)
            clientSocketTCP.sendall("teamTitans\n")
            gameMode(clientSocketTCP)          
        except:
            return
        
def listenUDP():  
  # get hostName and hostAdress and move it to tcpConn
    clientSocketUDP = socket.socket(socket.AF_INET , socket.SOCK_DGRAM)
    with clientSocketUDP:
        clientSocketUDP.bind('localhost', UDPPORT)
        print("Client started, listening for offer requests...")
        while True:
            clientSocketUDP.listen(1)
            modifiedMessage, serverAddress = clientSocketUDP.recvfrom(2048)
            print("Received offer from", serverAddress, "attempting to connect...")
            magicCookie , messageType, ServerPort = struct.unpack('ibH', modifiedMessage)
            if hex(magicCookie) == '0xabcddcba' and hex(messageType) == '0x2':
                server = Server(serverAddress, ServerPort)
                tcpConn(server)    
    
def main():
    listenUDP()


if __name__ == '__main__':
    main()