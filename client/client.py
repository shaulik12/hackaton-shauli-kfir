import socket 
import struct
import getch
from time import sleep

UDPPORT = 13117

class Server:
    def __init__(self, addr, port):
        self.addr = addr
        self.port = port 
    

def gameMode(clientSocketTCP):
    #get the q and give an a 
    try:
        msgQuestion = clientSocketTCP.recv(2048)   # wait for the question from the tcp server.
        msgQuestion = msgQuestion.decode(encoding = 'utf-8', errors='ignore')
        print(msgQuestion)
        answer = getch.getch()   # get one charcter from key
        answer = answer.encode(encoding= 'utf-8')
        clientSocketTCP.send(answer)
        msgSummery = clientSocketTCP.recv(2048)  # wait for summmery from the tcp server.
        msgSummery = msgSummery.decode(encoding = 'utf-8', errors='ignore')
        if len(msgSummery) == 0:
            print("Server disconnected, listening for offer requests...")
        else:
            print(msgSummery)
    except Exception as error:
            print("error: " , error)
            return
        
def TCPConn(server):
    #exstablish tcp connection and move to game mode
    clientSocketTCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  #make a tcp socket
    with clientSocketTCP:
        try:
            clientSocketTCP.connect((server.addr , server.port))   # connect to the tcp server
            TEAMNAME = "teamTitans\n"
            encode_teamName = TEAMNAME.encode(encoding='utf-8')
            clientSocketTCP.sendall(encode_teamName)  # send the team name to the tcp server
            gameMode(clientSocketTCP)      # start the game
        except Exception as error:
            print("error: " , error)
            return
        
def listenUDP():  
  # get hostName and hostAdress and move it to tcpConn
    clientSocketUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)    #make a udp socket
    with clientSocketUDP:
        clientSocketUDP.bind(("172.99.225.225", UDPPORT))        
        print("Client started, listening for offer requests...")
        while True:
            modifiedMessage, serverAddress = clientSocketUDP.recvfrom(2048)   # getting the broadcast message
            print("Received offer from", serverAddress[0], "attempting to connect...")
            try:
                magicCookie , messageType, ServerPort = struct.unpack('IbH', modifiedMessage)  #unpack the brodcast message to the matching pattern
                if hex(magicCookie) == '0xabcddcba' and hex(messageType) == '0x2':  # check prfix
                    server = Server(serverAddress[0], ServerPort)  # initial server address and server port
                    TCPConn(server)  # go to a function that will initial the tcp talk.
                    sleep(1)    # we sleep to not overflow the CPU   
            except Exception as error:
                print("error: ", error)
                sleep(1)    # we sleep to not overflow the CPU   
                pass
    
def main():
    listenUDP()

if __name__ == '__main__':
    main()