#-------------imports-------------
from random import randint
import socket
from time import sleep
import threading
import struct


#-------------constants-------------
HOSTIP = socket.gethostbyname(socket.gethostname())     #finds name of host running thethe program, then translates it to IP
UDPPORT = 13117             #predetermined udp listening port for clients
TCPPORT = 2086              #our team tcp port
GAMETIMEOUT = 10            #game wait timeout
MAXCLIENTS = 2              #maximum number of allowed clients
UDPFREQUENCY = 1            #delay between each UPD broadcast message
MAGICCOOKIE = 0xabcddcba    #UDP message confirmation cookie
OFFER = 0x2                 #UDP "offer" message flag


#-------------helper classes-------------
#holds all client related information
class Client:
    clientCountLock = threading.Lock()
    connected = 0
    def __init__(self, socket, addr):
        self.socket = socket
        self.addr = addr
        self.teamName = ""
    def setTeamName(self, teamName):
        self.teamName = teamName
        with Client.clientCountLock:
            Client.connected += 1
            if Client.connected >= MAXCLIENTS:
                gameStart.set()
    def disconnect(ansLock, client):
        print("player ", client.teamName, " disconnected")
        if not riddleAnswered.is_set():
            ansLock.giveAnswer(-1, client.teamName) #tell game the player no longer playes (gives impossible answer)
        try:
            connectedClients.remove(client)         #remove client from connected clients list
            with Client.clientCountLock:
                Client.connected -= 1
        finally:
            gameOver.set()                          #game no longer on max clients after 1one disconnects

#used to inform game thread all connected clients recieved its message        
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

#used to hold answer from the firs client to give it
#lock is only released in the game thread after winner is decided
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
        self.answer = ""
        self.player = ""
        try:
            self.lock.release()
        finally:
            return solution

#text coloration class using ANSI
class Color:
    END = '\033[0m'
    UNDERLINE = '\033[4m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = "\033[92m"
    YELLOW = "\033[33m"
    BLUE = "\033[94m"
    PURPLE = "\033[38;2;127;0;255m"
    ORANGE = "\033[38;2;255;135;70m"
    RAINDOW = [RED,ORANGE,YELLOW,GREEN,BLUE,PURPLE]
    TEAMCOLORS = [RED,BLUE]
    def makeRainbow(text):
        rainbowText = ""
        index = 0
        color = 0
        while index < len(text):
            if (text[index] != ' ') and (text[index] != '\n') and (text[index] != '\t'):
                textColor = Color.RAINDOW[color]
                rainbowText += f"{textColor}" + text[index]
                color += 1
                if color >= len(Color.RAINDOW):
                    color = 0
            else:
                rainbowText += text[index]
            index += 1
        rainbowText += f"{Color.END}"
        return rainbowText


#-------------shared resources and events-------------    
connectedClients = list()   #list of connected clients
threads = list()            #list of active threads
gameMsgUpdated = threading.Event()      #tells clients theres a new game message
clientsReady = threading.Event()        #all clients notify the game
riddleAnswered = threading.Event()      #tells the game a client has a solution
gameStart = threading.Event()           #tells the game it should start
gameOver = threading.Event()            #tells tcpInit the game has ended
underMaxClients = threading.Event()     #server has less than the maxium number of players connected
underMaxClients.set()


#-------------primary functions-------------    
#main function
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

#running UDP broadcast thread
def udpBroadcast():
    udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)    #creates a new socket
    with udpSocket:
        udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)     #at the socket level, set the broadcast option to 'on'
        #socketOptions(udpSocket)                                            #applies other socket option settings
        udpSocket.bind(('', 0))                                             #binds the socket to any available adress and port
        while True:
            if len(connectedClients) >= MAXCLIENTS:
                underMaxClients.wait()                                      #stop thread if max number of allowed clients are connected
            try:
                byteMsg = struct.pack('IbH', MAGICCOOKIE, OFFER, TCPPORT)   #creates message to be sent according to specified format
                udpSocket.sendto(byteMsg, ('<broadcast>',UDPPORT))          #attempts to send message
            except:
                print("exception occured during udp broadcast trasmission") #error in case message failed to transmit
            sleep(UDPFREQUENCY)                                             #sends broadcast message once a second

#tcp connection manager thread
def tcpInit(ansLock, gameMsgLock):
    tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   #creates TCP socket
    with tcpSocket:
        tcpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        tcpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #socketOptions(tcpSocket)                                    #sets basic socket options
        tcpSocket.bind(('', TCPPORT))                           #binds socket to our IP and port
        tcpSocket.listen(MAXCLIENTS)                                #accept conections form up to MAXCLIENTS amount of clients
        print("Server started, listening on IP address ", f"{Color.BOLD}{Color.UNDERLINE}", HOSTIP, f"{Color.END}")
        global connectedClients                                     #informs function this variable is announced globally
        while True:
            while len(connectedClients) < MAXCLIENTS:
                try:
                    conn, addr = tcpSocket.accept()                 #accepts connection
                    newClient = Client(conn,addr)
                    newThread = threading.Thread(target=tcpTalk, args=(newClient, ansLock, gameMsgLock))
                    newThread.setName("")
                    connectedClients.append(newClient)
                    global threads                                  #informs function this variable is announced globally 
                    threads.append(newThread)
                    newThread.start()
                except:
                    print("client of address ", addr, " failed to conect.")
            underMaxClients.clear()     #stops UDP broadcast
            gameStart.set()
            gameOver.wait()             #waits form game to end
            gameOver.clear()
            clearThreads()              #clean cleint specific threads
            if len(threads) < MAXCLIENTS:
                underMaxClients.set()   #informs UDP broadcast to continue

#tcp connection with specific client    
def tcpTalk(client, ansLock, gameMsgLock):
    with client.socket as socket:
        teamName = readTeamName(socket)         #get team name form the client
        print("player ", teamName, " has conected")
        threading.current_thread().setName(teamName)
        if teamName is not None:                #if connection hasn't ended
            client.setTeamName(teamName)        #sets the new team name
            gameMsgUpdated.wait()                #wait for game to give math question
            try:
                socket.sendall(gameMsgLock.gameMsg) #sends math question to client
                gameMsgLock.msgUsed(socket)         #inform game message was sent
                answer = readClientAnswer(socket)   #read user answer (only 1 character)
                if answer is not None:                      #if connection hasn't ended
                    ansLock.giveAnswer(answer,teamName)     #send answer to game
                    gameMsgUpdated.wait()                   #waits for game to give winner message
                    socket.sendall(gameMsgLock.gameMsg)     #sends game conclusion
            except:
                socket.close()
    Client.disconnect(ansLock, client)

#game thread in charge of generating messages for clients and deciding winners    
def game(answerLock, gameMsgLock):
    while True:
        gameStart.wait()                   #wait until 2 clients are conected
        sleep(GAMETIMEOUT)                 #after second client connects, wait 10 seconds for game to begin
        try:
            teamNames = [conn.teamName for conn in connectedClients]
            riddle, ans = mathGenerator()   #generate simple math riddle and answer
            startMsg = gameStartMessage(teamNames, riddle)
            gameMsgLock.setMsg(startMsg)    #tells clients to send the message
            isDraw = not riddleAnswered.wait(GAMETIMEOUT)  #waiting for riddle answer or 10 seconds
            riddleAnswered.clear()
            solver, guess = answerLock.checkSolution()
            if guess != ans:
                solver = [team for team in teamNames if team != solver]
                if len(solver) == 0:
                    isDraw = True
                else:
                    solver = solver[0]
            endMsg = gameOverMessage(isDraw, solver, ans)
            gameMsgLock.setMsg(endMsg) 
            print(f"{Color.RED}{Color.BOLD}Game over, sending out offer requests...{Color.END}")
        finally:
            gameStart.clear()                  #tells tcpInit thread the game ended nad clients are logged out
            gameOver.set()


#-------------helper functions-------------
#generates colorful welcome message containing the question the players need to answer  
def gameStartMessage(teamNames, riddle):
    msg = "Welcome to Quick Maths.\n"
    msg = Color.makeRainbow(msg)
    for indx in range(len(teamNames)):
        teamColor = Color.TEAMCOLORS[indx]
        teamName = f"{teamColor}" + teamNames[indx]
        msg += f"{Color.YELLOW}Player " + str(indx+1) + ": " + teamName + "\n"
    msg += "==\n"
    request = "Please answer the following question as fast as you can:\n"
    request = Color.makeRainbow(request)
    msg += request
    msg += "How much is " + riddle + "?"
    buffer = msg.encode(encoding='utf-8')
    return buffer

#generates colorful message informing players the game ended and who the winner is
def gameOverMessage(isDraw, solver, riddleAns):  
    msg = "Game over!\n"
    msg += "The correct answer was " + str(riddleAns) + "!\n"
    if isDraw:
        msg += "Congratulations, the game is a draw"
    else:
        msg += "Congratulations to the winner: " + solver
    buffer = msg.encode(encoding='utf-8')
    return buffer

#generates random simple math question
def mathGenerator():
    operand = ["+","-"]
    a = randint(1, 9)
    b = randint(1, 9)
    randop = randint(0, 1)
    riddle = str(a) + operand[randop] + str(b)
    res = eval(riddle)
    if res > 9:                         #if generated question results in an answer thats more than one digit
        c = randint(res-9, 9)
        res -= c
        riddle = riddle + "-" + str(c)
    elif res < 0:                       #if generated question results in an answer thats a negative number
        c = randint((res*(-1)), 9)
        res += c
        riddle = riddle + "+" + str(c)
    return (riddle,res)                 #returns tupple containig riddle and answer

#sets basic necesary socket options
def socketOptions(mySocket):
    mySocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    mySocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    mySocket.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, 'eth1')

#reads client team name
def readTeamName(clientSocket):
    buffer = b''                            #client message accumulator
    while b'\n' not in buffer:              #wait for newline delimiter to stop listening
        try:
            recieved = clientSocket.recv(1024)  #reading message form client (blocking)
            if not recieved:
                return None                     #connection ended
            buffer += recieved                  #accumulates potentially long meesage
        except:
            return None
    decoded = buffer.decode(encoding='utf-8', errors='ignore')  #convert message from bytes to string
    teamName, seperator, remainder = decoded.partition('\n')    #partition client message according to \n
    return teamName

#reads riddle answer from client
def readClientAnswer(clientSocket):
    while True:
        ansBytes = clientSocket.recv(1)         #recieve 1 character from client
        if not ansBytes:
            return None                         #if message empty, returns None to notify the connection ended
        ans = bytes(ansBytes).decode(encoding='utf-8', errors='ignore') #decoded client string response
        return ans

#delets all still living client specific threads when the game ends
def clearThreads():
    global threads
    global connectedClients
    threads = [t for t in threads if t.is_alive()]  #goes over every still living client threads
    for thread in threads:
        stuckClients = [client for client in connectedClients if client.teamName == thread.getName()]   #finds client objects related to those threads
        for client in stuckClients:
            client.socket.close()                   #closes the client related socket to cause thread to end
        thread.join()                               #will cause tcpInit to wait for all clients to close
 
if __name__ == '__main__':
    Main()
