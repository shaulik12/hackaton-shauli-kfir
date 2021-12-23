from socket import *

HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
UDPPORT = 65432        # Port to listen on (non-privileged ports are > 1023)

def server():
    s = socket.socket(AF_INET, SOCK_DGRAM)
    with s:
        s.bind((HOST, UDPPORT))
        s.listen()
        conn, addr = s.accept()
        with conn:
            print('Connected by', addr)
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                conn.sendall(data)