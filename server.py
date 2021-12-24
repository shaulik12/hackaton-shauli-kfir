from random import randint
import socket
from time import sleep
import threading
import struct
#from scapy import *

HOSTIP = '127.0.0.1'
#get_if_addr('eth1')
UDPPORT = 13117

class Client:
    def __init__(self, socket, addr):
        self.socket = socket
        self.addr = addr
        self.teamName = ""
    def addTeamName(self, teamName):
        self.teamName = teamName

tcpPort = -1
connectedClients = list()
threads = list()
under2Clients = threading.Event()
under2Clients.set()
maxClients = threading.Event()
maxClients.clear()
waitingRiddleAnswer = threading.Event()
waitingRiddleAnswer.clear()


def server():
    broadcastThread = threading.Thread(target=udpBroadcast)
    tcpThread = threading.Thread(target=tcpInit)
    gameThread = threading.Thread(target=tcpInit)
    gameThread.start()
    tcpThread.start()
    broadcastThread.start()
    gameThread.join()
    tcpThread.join()
    broadcastThread.join()

def tcpInit():
    tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    with tcpSocket:
        tcpSocket.bind((socket.gethostname(),0))
        tcpPort = tcpSocket.getsockname()[1]
        tcpSocket.listen(2)
        while True:
            while len(connectedClients) < 2:
                clientSocket, addr = tcpSocket.accept()
                newClient = Client(clientSocket,addr)
                connectedClients.append(newClient)
                thread = threading.Thread(target=tcpTalk, args=(newClient,))
                connectedClients.append(newClient)               
                threads.append(thread)
                thread.start()
            maxClients.set()
            under2Clients.clear()
            #TODO---------------------------------------------------------------
            under2Clients.wait()
            threads = [t for t in threads if t.is_alive()]
            if len(threads) < 2:
                maxClients.clear()
            #TODO---------------------------------------------------------------


#TODO---------------------------------------------------------------
def tcpTalk(client):
    with client.socket as s:
        data = s.recv(2048)
        data = data.decode('utf-8')
        if data[-1] == '\n':
            client.addTeamName(data)
    connectedClients.remove(client)
    under2Clients.set()
#TODO---------------------------------------------------------------

def udpBroadcast():
    udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    with udpSocket:
        udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)    #at the socket level, set the broadcast option to 'on'
        #udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)    #run on linux
        udpSocket.bind(("", 0))
        print("Server started, listening on IP address ", HOSTIP) 
        while True and tcpPort != (-1):
            if len(connectedClients) >= 2:
                under2Clients.wait()
            try:
                byteMsg = struct.pack('LbH', 0xabcddcba, 0x2, tcpPort)
                udpSocket.sendall(byteMsg, ('<broadcast>',UDPPORT))
            except:
                print("exception occured during udp broadcast trasmission")
            sleep(1)    #sends message once a second

def game():
    while True:
        maxClients.wait()
        sockets = [conn.socket for conn in connectedClients]
        with (s for s in sockets):
            teamNames = [conn.teamName for conn in connectedClients]
            math = mathGenerator()
            msg = gameMessage(teamNames, math[0])
            for s in sockets:
                s.sendall(msg)
            waitingRiddleAnswer.clear()
            answered = waitingRiddleAnswer.wait(10.0)
            #TODO---------------------------------------------------------------
            if answered:
                print("not time out")
            else:
                print("not time out")
            #TODO---------------------------------------------------------------

def gameMessage(teams, riddle):
    msg = "Welcome to Quick Maths."
    for i in range(len(teams)):
        msg += "\nPlayer " + i + ": " + teams[i].teamName
    msg += "\n=="
    msg += "\nPlease answer the following question as fast as you can:\n"
    msg += "How much is" + riddle + "?\n"
    return msg

def mathGenerator():
    operand = ["+","-"]
    a = randint(1, 9)
    b = randint(1, 9)
    randop = randint(0, 1)
    riddle = str(a) + operand[randop] + str(b)
    res = eval(riddle)
    if res > 9:
        c = randint(res-9, 9)
        res -= c
        riddle = riddle + "-" + str(c)
    elif res < 0:
        c = randint((res*(-1)), 9)
        res += c
        riddle = riddle + "+" + str(c)
    return (riddle,res)


if __name__ == '__main__':
    server()