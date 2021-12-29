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
    except Exception as error:
            print("error3 = " , error)
            return
    
def TCPConn(server):
    #exstablish tcp connection and move to game mode
    clientSocketTCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    with clientSocketTCP:
        try:
            # clientSocketTCP.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, 'eth1')
            clientSocketTCP.connect((server.addr , server.port))
            TEAMNAME = "teamTitans\n"
            encode_teamName = TEAMNAME.encode(encoding='utf-8')
            clientSocketTCP.sendall(encode_teamName)
            gameMode(clientSocketTCP)          
        except Exception as error:
            print("error2 = " , error)
            return
        
def listenUDP():  
  # get hostName and hostAdress and move it to tcpConn
    clientSocketUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    with clientSocketUDP:
        clientSocketUDP.bind(('', UDPPORT))
        print("Client started, listening for offer requests...")
        while True:
            modifiedMessage, serverAddress = clientSocketUDP.recvfrom(2048)
            print("Received offer from", serverAddress[0], "attempting to connect...")
            try:
                magicCookie , messageType, ServerPort = struct.unpack('IbH', modifiedMessage)
                if hex(magicCookie) == '0xabcddcba' and hex(messageType) == '0x2':
                    server = Server(serverAddress[0], ServerPort)
                    TCPConn(server)  
                    sleep(0.5)
            except Exception as error:
                print("error1 = ", error) 
            finally:
                sleep(1)       
    
def main():
    listenUDP()


if __name__ == '__main__':
    main()