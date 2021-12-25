from server import gameStartMessage
from server import gameOverMessage
from time import sleep
from random import randint
import struct
import unittest
import threading

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
    
def main():
    #Tests.messagesTest()
    #Tests.nonblockingLockTest()
    #Tests.blockingLockTest()
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