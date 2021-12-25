from random import randint
import socket
from time import sleep
import threading
import struct
#from scapy.arch import get_if_addr

HOSTIP = '127.0.0.1' #get_if_addr('eth1')
UDPPORT = 13117
DRAW = -1
GAMETIMEOUT = 10
MAXCLIENTS = 2
UDPFREQUENCY = 1
MAGICCOOKIE = 0xabcddcba
OFFER = 0x2

class Client:
    def __init__(self, socket, addr):
        self.socket = socket
        self.addr = addr
        self.teamName = ""
    def setTeamName(self, teamName):
        self.teamName = teamName
        
class GameMsgLock:        
    def __init__(self):
        self.gameMsg = ""
        self.clientsUsedMsg = 0
        self.msgLock = threading.Lock()
    def setMsg(self, msg):
        self.gameMsg = msg
        self.clientsUsedMsg = 0
        gameMsgUpdate.set()
    def msgUsed(self):
        with self.msgLock:
            self.clientsUsedMsg += 1
            if (self.clientsUsedMsg >= MAXCLIENTS):
                gameMsgNotify.set()

class AnswerLock:
    def __init__(self):
        self.answer = ""
        self.player = ""
        self.lock = threading.Lock()
    def giveAnswer(self, ans, ply):
        locked = self.lock.acquire(False)
        if locked:
            self.answer = ans
            self.player = ply
            riddleAnswered.set()
    def checkSolution(self):
        solution = (self.player, self.answer)
        try:
            self.lock.release()
        finally:
            return solution

tcpPort = -1                #TCP port used for communication
connectedClients = list()   #list of connected clients
threads = list()            #list of active threads
tcpPortInitialized = threading.Event()  #tells UPD transmitted that the TCP port is initialized
gameMsgUpdate = threading.Event()       #tells clients theres a new game message
gameNotPlayed = threading.Event()            #notifies clients the game is over
gameMsgNotify = threading.Event()       #tells game all clients got the message
riddleAnswered = threading.Event()      #tells the game a client has a solution
maxClients = threading.Event()          #maxium number of clients reached
underMaxClients = threading.Event()     #server has less than the maxium number of players connected
underMaxClients.set()
gameNotPlayed.set()

def Main():
    ansLock = AnswerLock()
    gameMsgLock= GameMsgLock()
    broadcastThread = threading.Thread(target=udpBroadcast)
    tcpThread = threading.Thread(target=tcpInit, args=(ansLock, gameMsgLock))
    gameThread = threading.Thread(target=game, args=(ansLock, gameMsgLock))
    gameThread.start()
    tcpThread.start()
    broadcastThread.start()
    gameThread.join()
    tcpThread.join()
    broadcastThread.join()

def tcpInit(ansLock, gameMsgLock):
    tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    with tcpSocket:
        tcpSocket.bind((socket.gethostname(),0))
        global tcpPort
        tcpPort = tcpSocket.getsockname()[1]
        tcpSocket.listen(MAXCLIENTS)
        print("Server started, listening on IP address ", HOSTIP) 
        tcpPortInitialized.set()
        while True:
            while len(connectedClients) < MAXCLIENTS:
                conn, addr = tcpSocket.accept()
                newClient = Client(conn,addr)
                newThread = threading.Thread(target=tcpTalk, args=(newClient, ansLock, gameMsgLock))
                connectedClients.append(newClient)               
                threads.append(newThread)
                newThread.start()
            maxClients.set()            #notify max number of clients is reached
            underMaxClients.clear()
            gameNotPlayed.wait()      #wait until the game has ended
            gameNotPlayed.clear()
            threads = [t for t in threads if t.is_alive()]  #clean dead threads
            if len(threads) < MAXCLIENTS:
                maxClients.clear()
            print("Game over, sending out offer requests...")
            
#TODO---------------------------------------------------------------
def tcpTalk(client, ansLock, gameMsgLock):
    while True:
        with client.socket as s:
            inpt = s.recv(2048)
            inpt = inpt.decode('utf-8')
            if not inpt:
                break
            elif inpt[-1] == '\n':
                client.addTeamName(inpt)
            
        connectedClients.remove(client)
        underMaxClients.set()
#TODO---------------------------------------------------------------

def game(answerLock, gameMsgLock):
    while True:
        maxClients.wait()                   #wait until 2 clients are conected
        sleep(GAMETIMEOUT)                  #after second client connects, wait 10 seconds for game to begin
        sockets = [conn.socket for conn in connectedClients]
        with (s for s in sockets):
            riddleAnswered.clear()
            teamNames = [conn.teamName for conn in connectedClients]
            riddle, ans = mathGenerator()   #generate simple math riddle and answer
            startMsg = gameStartMessage(teamNames, riddle)
            gameMsgLock.setMsg(startMsg)
            gameMsgNotify.wait()            #waiting for game message to be sent to all clients
            gameMsgNotify.clear()
            isDraw = not riddleAnswered.wait(GAMETIMEOUT)  #waiting for riddle answer or 10 seconds
            solver, guess = answerLock.checkSolution()
            if guess != ans:
                teamNames.remove(solver)
                solver = teamNames[0]
            endMsg = gameOverMessage(isDraw, solver, ans)
            gameMsgLock.setMsg(endMsg) 
            gameMsgNotify.wait()            #waiting for message to be sent and clients to log out. prevents game restart
            gameMsgNotify.clear()
            gameNotPlayed.set()                  #tells tcpInit thread the game ended nad clients are logged out

def gameStartMessage(teamNames, riddle):
    msg = "Welcome to Quick Maths.\n"
    for indx in range(len(teamNames)):
        msg += "Player " + str(indx+1) + ": " + teamNames[indx] + "\n"
    msg += "==\n"
    msg += "Please answer the following question as fast as you can:\n"
    msg += "How much is " + riddle + "?"
    return msg

def gameOverMessage(isDraw, solver, riddleAns):  
    msg = "Game over!\n"
    msg += "The correct answer was " + str(riddleAns) + "!\n"
    if isDraw:
        msg += "Congratulations, the game is a draw"
    else:
        msg += "Congratulations to the winner: " + solver
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

def udpBroadcast():
    udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    with udpSocket:
        udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)     #at the socket level, set the broadcast option to 'on'
        #udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)    #run on linux
        udpSocket.bind(("", 0))
        tcpPortInitialized.wait()                                           #waits for TCP port to initialize
        while True:
            if len(connectedClients) >= MAXCLIENTS:
                underMaxClients.wait()                                      #stop threat if max clients connected
            try:
                byteMsg = struct.pack('IbH', MAGICCOOKIE, OFFER, tcpPort)   #creates message to be sent
                udpSocket.sendto(byteMsg, ('<broadcast>',UDPPORT))          #attempts to send message
            except:
                print("exception occured during udp broadcast trasmission")
            sleep(UDPFREQUENCY)                                             #sends message once a second

if __name__ == '__main__':
    Main()
