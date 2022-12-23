from MultiThreadServerClass import MultiThreadServer
from threading import Thread
import mediapipe as mp
import socket

# 생성된 쓰레드에서 반복적으로 처리할 함수
# 클라이언트에서 데이터가 수신되면 서버는 요청을 처리하고 처리 결과 데이터에 따라 특정 클라이언트에 데이터를 송신한다 .
def tcpHandler(server : MultiThreadServer, cSock : socket.socket):
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles
    mp_face_mesh = mp.solutions.face_mesh

    with mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5) as face_mesh:
        while True:
            headerBytes, dataBytesList = server.receive(cSock)
            if headerBytes is None and dataBytesList is None:
                break
            response = server.processData(
                cSock=cSock, headerBytes=headerBytes, dataBytesList=dataBytesList, 
                mp_face_mesh=mp_face_mesh, 
                face_mesh=face_mesh,
                mp_drawing=mp_drawing,
                mp_drawing_styles = mp_drawing_styles
            )
            if not response is None:
                server.send(cSock, response)

def udpHandler(server : MultiThreadServer):
    while True:
        headerBytes, dataBytesList = server.receive(cSock)
        if headerBytes is None and dataBytesList is None:
            break
        response = server.processData(
            cSock=cSock, headerBytes=headerBytes, dataBytesList=dataBytesList, 
            mp_face_mesh=mp_face_mesh, 
            face_mesh=face_mesh,
            mp_drawing=mp_drawing,
            mp_drawing_styles = mp_drawing_styles
        )
        if not response is None:
            server.send(cSock, response)

server = MultiThreadServer(port = 2500, listener = 100) # TCPMultiThreadServer 서버 객체 생성

# 무한 루프
# 서버는 항상 클라이언트 연결을 대기한다
while True:
    print("waiting for connection...")
    cSock, addr = server.accept() # 서버에 연결된 클라이언트가 존재하면 클라이언트에 연결된 소켓과 클라이언트의 어드레스를 반환한다.
    cThread = Thread(target=tcpHandler, args=(server, cSock)) # 연결된 클라이언트에 대한 쓰레드 생성
    cThread.daemon = True # 생성된 쓰레드의 데몬 여부를 True로 한다. (데몬 스레드 = 메인 스레드가 종료되면 즉시 종료되는 스레드)
    cThread.start() # 쓰레드 시작
    print(server.clients)