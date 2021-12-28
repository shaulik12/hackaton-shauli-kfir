from random import randint
import socket
from time import sleep
import threading
import struct

HOSTIP = socket.gethostbyname(socket.gethostname())     #finds name of host running thethe program, then translates it to IP
UDPPORT = 13117             #predetermined udp listening port for clients                  
GAMETIMEOUT = 10            #game wait timeout
MAXCLIENTS = 2              #maximum number of allowed clients
UDPFREQUENCY = 1            #delay between each UPD broadcast message
MAGICCOOKIE = 0xabcddcba    #UDP message confirmation cookie
OFFER = 0x2                 #UDP "offer" message flag

class Client:
    def __init__(self, socket, addr):
        self.socket = socket
        self.addr = addr
        self.teamName = ""
    def setTeamName(self, teamName):
        self.teamName = teamName
    def disconnect(ansLock, client):
        clientsReady.set()     #tells game to stop waiting
        if not riddleAnswered.is_set():
            ansLock.giveAnswer(-1, client.teamName) #tell game the player no longer playes (gives impossible answer)
        connectedClients.remove(client)     #remove client from connected clients list
        gameNotPlayed.set()   #game no longer on max clients after 1one disconnects
        
     
class GameMsgLock:        
    def __init__(self):
        self.gameMsg = ""
        self.clientsUsedMsg = 0
        self.msgLock = threading.Lock()
    def setMsg(self, msg):
        self.gameMsg = msg
        self.clientsUsedMsg = 0
        gameMsgUpdated.set()
    def msgUsed(self):
        with self.msgLock:
            self.clientsUsedMsg += 1
            if (self.clientsUsedMsg >= MAXCLIENTS):
                gameMsgUpdated.clear()
                clientsReady.set()

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
gameMsgUpdated = threading.Event()      #tells clients theres a new game message
#gameNotPlayed = threading.Event()           #tells clients the game is over
clientsReady = threading.Event()        #all clients notify the game
riddleAnswered = threading.Event()      #tells the game a client has a solution
gameStart = threading.Event()           #tells the game it should start
underMaxClients = threading.Event()     #server has less than the maxium number of players connected
underMaxClients.set()
#gameNotPlayed.set()

# add extention "remove ssh"
#choose the hackaton from the configuration file on the search bar on top
#then open file

#on client: tcpSocket.setsockopt(socket.SOL_SOCKET, socket.TCP_NODELAY, 1)

def Main():
    ansLock = AnswerLock()
    gameMsgLock = GameMsgLock()
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
        tcpSocket.bind((HOSTIP,0))
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
                underMaxClients.set()
            print("Game over, sending out offer requests...")
            
def tcpTalk(client, ansLock, gameMsgLock):
    with client.socket as socket:
        teamName = readTeamName(socket)         #get team name form the client
        if teamName is not None:                #if connection hasn't ended
            client.setTeamName(teamName)        #sets the new team name
            gameMsgUpdated.wait()                #wait for game to give math question
            socket.sendall(gameMsgLock.gameMsg) #sends math question to client
            gameMsgLock.msgUsed(socket)         #inform game message was sent
            answer = readClientAnswer(socket)   #read user answer (only 1 character)
            if answer is not None:                      #if connection hasn't ended
                ansLock.giveAnswer(answer,teamName)     #send answer to game
                gameMsgUpdated.wait()                    #waits for game to give winner message
                socket.sendall(gameMsgLock.gameMsg)     #sends game conclusion
    Client.disconnect(client)

def readTeamName(clientSocket):
    buffer = b''                            #client message accumulator
    while b'\n' not in buffer:              #wait for newline delimiter to stop listening
        recieved = clientSocket.recv(1024)  #reading message form client (blocking)
        if not recieved:
            return None                         #connection ended
        buffer += recieved                  #accumulates potentially long meesage
    decoded = buffer.decode(encoding='utf-8', errors='ignore')  #convert message from bytes to string
    teamName, seperator, remainder = decoded.partition('\n')    #partition client message according to \n
    return teamName

def readClientAnswer(clientSocket):
    while True:
        ansBytes = clientSocket.recv(1)
        if not ansBytes:
            return None
        ans = bytes(ansBytes).decode(encoding='utf-8', errors='ignore')
        return ans
             
def game(answerLock, gameMsgLock):
    while True:
        gameStart.wait()                   #wait until 2 clients are conected
        #TODO wait until all connected clients set their name
        sleep(GAMETIMEOUT)                  #after second client connects, wait 10 seconds for game to begin
        try:
            teamNames = [conn.teamName for conn in connectedClients]
            riddle, ans = mathGenerator()   #generate simple math riddle and answer
            startMsg = gameStartMessage(teamNames, riddle)
            gameMsgLock.setMsg(startMsg)    #tells clients to send the message
            clientsReady.wait()            #waiting for game message to be sent to all clients
            clientsReady.clear()
            isDraw = not riddleAnswered.wait(GAMETIMEOUT)  #waiting for riddle answer or 10 seconds
            riddleAnswered.clear()
            solver, guess = answerLock.checkSolution()
            if guess != ans:
                teamNames.remove(solver)
                solver = teamNames[0]
            endMsg = gameOverMessage(isDraw, solver, ans)
            gameMsgLock.setMsg(endMsg) 
            clientsReady.wait()            #waiting for message to be sent and clients to log out. prevents game restart
        finally:
            clientsReady.clear()
            gameStart.clear()                  #tells tcpInit thread the game ended nad clients are logged out

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
