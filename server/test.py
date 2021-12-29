from server import gameStartMessage
from server import gameOverMessage
from time import sleep
from random import randint
import struct
import unittest
import threading
import socket

#https://gist.github.com/fnky/458719343aabd01cfb17a3a4f7296797
class Color:
    END = '\033[0m'
    UNDERLINE = '\033[4m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = "\033[92m"
    YELLOW = "\033[33m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    ORANGE = "\033[38;2;255;135;70m"
    RAINDOW = [RED,ORANGE,YELLOW,GREEN,BLUE,MAGENTA]
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
        

class NonBlockingLock:
    def __init__(self):
        self.aThread = ""
        self.lock = threading.Lock()
    def activate(self, aThread):
        acq = self.lock.acquire(False) 
        if acq:          
            self.aThread = aThread
            print("got by ", aThread)
        return acq

class BlockingLock:
    def __init__(self):
        self.counter = 0
        self.lock = threading.Lock()
    def incrementSafe(self):
        with self.lock:
            self.counter += 1
    def incrementUnsafe(self):
        self.counter += 1
    def reset(self):
        self.counter = 0

class Unitests(unittest.TestCase):
    def byteTest(self):
        byteMsg = struct.pack('IbH', 0xabcddcba, 0x2, 7654)
        unbyteMsg = struct.unpack('IbH', byteMsg)
        self.assertTrue(hex(unbyteMsg[0])==0xabcddcba)
        self.assertTrue(unbyteMsg[2]==7654)

class Tests:
    def messagesTest():
        teamNames = ["Instinct", "Rocket"]
        rid = "2+2-1"
        ans = 3
        print(gameStartMessage(teamNames, rid))
        print(gameOverMessage(teamNames, -1, ans))

    def nonblockingLockTest():
        mylock = NonBlockingLock()
        main_thread = threading.currentThread()
        for i in range(5):
            t = threading.Thread(target=Tests.threadcall, args=(mylock, str(i)))
            t.start()
        sleep(3)
        print("first to take lock was: ", mylock.aThread)
        mylock.lock.release()
        for t in threading.enumerate():
            if t is not main_thread:
                t.join()      
        print("just making sure the last to take lock was: ", mylock.aThread)

    def threadcall(mylock, myName):
        sleepTime = randint(1,5) * 0.1
        sleep(sleepTime)
        aq = mylock.activate(myName)
        print("did", myName, " get lock? ", str(aq))

    def blockingLockTest():
        mylock = BlockingLock()
        main_thread = threading.currentThread()
        for i in range(10):
            t = threading.Thread(target=Tests.inc, args=(mylock,))
            t.start()
        for t in threading.enumerate():
            if t is not main_thread:
                t.join()      
        print("counter at ", str(mylock.counter))

    def inc(mylock):
        sleep(0.1)
        for i in range(100000):
            mylock.incrementSafe()
    
    def colorTest1():
        msg = f"{Color.ORANGE}Notice:"
        msg += f"{Color.RED} you color"
        msg += f"{Color.YELLOW} has changed"
        msg += f"{Color.END}"
        print(msg)
    
    def colorTest2():
        msg = "welcome to the game\nnew player!"
        msg = Color.makeRainbow(msg)
        print(msg)
  
    def socketTest():
        ip = socket.gethostbyname(socket.gethostname())
        print(ip)
    
    def bufferTest():
        buffer = b''
        message = "hello my name is X\nx\nyou"
        buffer += message.encode(encoding='utf-8')
        print("buffer is: ", buffer)
        decoded = buffer.decode(encoding='utf-8', errors='ignore')
        relevant = decoded.partition('\n')
        print("relevant is: ", relevant[0])
        
def main():
    #Tests.messagesTest()
    #Tests.nonblockingLockTest()
    #Tests.blockingLockTest()
    Tests.colorTest2()
    #Tests.socketTest()
    #Tests.bufferTest()
    print()

if __name__ == '__main__':
    main()
    
    
    
    
#https://pythonprogramming.net/sockets-tutorial-python-3/
#https://realpython.com/python-sockets/#echo-server
#https://realpython.com/python-sockets/#echo-server
#https://www.geeksforgeeks.org/socket-programming-multi-threading-python/
#https://www.positronx.io/create-socket-server-with-multiple-clients-in-python/
#https://coddingbuddy.com/article/58480889/python-socket-multiple-clients
#https://www.bogotobogo.com/python/python_network_programming_tcp_server_client_chat_server_chat_client_select.php
#https://docs.python.org/3/howto/sockets.html