import socket
from response import *

port = 2500
listener = 600

tcpSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # 서버 TCP 소켓 생성
udpSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # 서버 UDP 소켓 생성
tcpSock.bind(('', port)) # 서버 소켓에 어드레스(IP가 빈칸일 경우 자기 자신(127.0.0.1)로 인식한다. + 포트번호)를 지정한다.
udpSock.bind(('', port + 1))
tcpSock.listen(listener) # 서버 소켓을 연결 요청 대기 상태로 한다.

cSock, cAddr = tcpSock.accept() # 클라이언트와 연결이 된다면 클라이언트와 연결된 소켓과 클라이언트의 어드레스(IP와 포트번호)를 반환한다.
print(f"connection {cAddr}" )

byte, addr = udpSock.recvfrom(1024)
print(byte)
print(addr)
byte, addr = udpSock.recvfrom(1024)
print(byte)
print(addr)

resChat = ResChat("dddd")
totalBytes = resChat.totalBytes()

udpSock.sendto(len(totalBytes).to_bytes(4, "little"), addr)
udpSock.sendto(totalBytes, addr)

# cSock.sendall(len(totalBytes).to_bytes(4, "little"))
# cSock.sendall(totalBytes)

while True:
    pass