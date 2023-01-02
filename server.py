import socket
from request import *
from response import *
from threading import Thread

class ClientData:
    def __init__(self):
        self.id : str = ""
        self.udpAdr : tuple[str, int] = None
        self.roomMaster : socket.socket = None
        self.noFaceCount : int = 0
        self.eyeBlinkCount : int = 0
        self.otherDirectionCount : int = 0
#   {
#       "id" : "아이디",
#       "udpAdr" : udp 소켓의 어드레스(ip + 포트)
#       "roomMaster" : 방장 소켓,
#       "noFaceCount" : 얼굴 존재 카운트 = 0, 
#       "eyeBlinkCount" : 눈깜박임 체크 카운트 = 0, 
#       "otherDirectionCount" : 다른 방향 체크 카운트 = 0
#   }

class RoomData:
    def __init__(self, roomName : str = ""):
        self.roomName : str = roomName
        self.roomMemberList : list[socket.socket] = []
#   {
#       "name" : "방 이름",
#       "roomMember" : [참가 인원의 소켓],
#   }


UDPSockList : dict[tuple[str, int], socket.socket] = {}
clients : dict[socket.socket, ClientData] = {}
roomList : dict[socket.socket, RoomData] = {}

def receiveTCP(sock : socket.socket):
    while True:
        try:
            # receive tcp data
            dataSize : int = int.from_bytes(sock.recv(4), "little")
            recvSize : int = 0
            rawData : bytearray = bytearray()
            while recvSize < dataSize:
                packetSize = 1024 if recvSize + 1024 < dataSize else dataSize - recvSize
                packet = sock.recv(packetSize)
                rawData.extend(packet)
                recvSize += packetSize
            
            # change rawData to request tcp class
            reqtcp = RequestTCP(rawData)

            # 
            restcp = None
            if reqtcp.requsetType == RequestType.UDPConnect.value:
                reqtcp = ReqUDPConnect(reqtcp)
                UDPSockList[(reqtcp.servIp, reqtcp.port)] = sock
                clients[sock].udpAdr = (reqtcp.servIp, reqtcp.port)
                # restcp = ResChat("dddssddddd")
            
            if not restcp is None:
                totalBytes = bytearray()
                totalBytes.extend(restcp.totalSizeByte())
                totalBytes.extend(restcp.headerBytes)
                totalBytes.extend(restcp.dataBytes)
                sock.sendall(totalBytes)

        except Exception as e:
            print(e)
            if not clients[sock].udpAdr is None:
                del UDPSockList[clients[sock].udpAdr]
            del clients[sock]
            sock.close()
            print(f"{clients}")
            print(f"clients Count : {len(clients)}")
            break

def receiveUDP(sock: socket.socket):
    while True:
        try:
            # receive udp data
            rawData, addr = sock.recvfrom(4 + 4 + 1024)
            if not addr in UDPSockList:
                raise

            # change raw data to request tcp class
            requdp = RequestUDP(rawData)

            resudp = None
            if requdp.requsetType == RequestType.Image.value:
                resudp = ResImage(requdp)

            if not resudp is None:
                totalBytes = bytearray()
                totalBytes.extend(resudp.headerBytes)
                totalBytes.extend(resudp.dataBytes)
                sock.sendto(totalBytes, addr)
        except:
            pass

port = 2500
listener = 600

tcpSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # 서버 TCP 소켓 생성
tcpSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # alreay in use 방지용
tcpSock.bind(('', port)) # 서버 소켓에 어드레스(IP가 빈칸일 경우 자기 자신(127.0.0.1)로 인식한다. + 포트번호)를 지정한다.
tcpSock.listen(listener) # 서버 소켓을 연결 요청 대기 상태로 한다.

udpSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # 서버 UDP 소켓 생성
udpSock.bind(('', port + 1))
udpThread = Thread(target=receiveUDP, args=(udpSock, )) # 연결된 클라이언트에 대한 쓰레드 생성
udpThread.daemon = True # 생성된 쓰레드의 데몬 여부를 True로 한다. (데몬 스레드 = 메인 스레드가 종료되면 즉시 종료되는 스레드)
udpThread.start() # 쓰레드 시작

while True:
    print("waiting for clients...")
    cSock, cAddr = tcpSock.accept() # 클라이언트와 연결이 된다면 클라이언트와 연결된 소켓과 클라이언트의 어드레스(IP와 포트번호)를 반환한다.
    clients[cSock] = ClientData()
    cThread = Thread(target=receiveTCP, args=(cSock, )) # 연결된 클라이언트에 대한 쓰레드 생성
    cThread.daemon = True # 생성된 쓰레드의 데몬 여부를 True로 한다. (데몬 스레드 = 메인 스레드가 종료되면 즉시 종료되는 스레드)
    cThread.start() # 쓰레드 시작
    print(f"clients Count : {len(clients)} / connection {cAddr}")