import socket
import cv2
from dataheader import *
from db import DB
from mediapipe.python.solutions import face_mesh as F, drawing_styles as D
import predictEye
import predictAngle


class MultiThreadServer:
    def __init__(self, port : int = 2500, listener : int = 600):
        self.db = DB()
        self.connected = False # 서버가 클라이언트와 연결되었는지를 판단하는 변수
        
        self.clients : dict[socket.socket, dict] = {} # 현재 서버에 연결된 클라이언트 정보를 담는 변수
        # ex) 
        # { 클라이언트 소켓 : 
        #   {
        #       "id" : "아이디",
        #       "roomMaster" : 방장 소켓,
        #       "noFaceCount" : 얼굴 존재 카운트 = 0, 
        #       "eyeBlinkCount" : 눈깜박임 체크 카운트 = 0, 
        #       "otherDirectionCount" : 다른 방향 체크 카운트 = 0
        #   }
        # }

        self.roomList : dict[socket.socket, tuple[str, list[socket.socket]]] = {} # 현재 생성된 방의 정보를 담는 변수
        # ex)
        # { 클라이언트 소켓 : 
        #   {
        #       "name" : "방 이름",
        #       "roomMember" : [참가 인원의 소켓],
        #   }
        # }
        
        self.tcpSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # 서버 TCP 소켓 생성
        self.udpSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # 서버 UDP 소켓 생성
        self.tcpSock.bind(('', port)) # 서버 소켓에 어드레스(IP가 빈칸일 경우 자기 자신(127.0.0.1)로 인식한다. + 포트번호)를 지정한다.
        self.udpSock.bind(('', port + 1))
        self.tcpSock.listen(listener) # 서버 소켓을 연결 요청 대기 상태로 한다.

    # 클라이언트 연결
    def accept(self):
        cSock, cAddr = self.tcpSock.accept() # 클라이언트와 연결이 된다면 클라이언트와 연결된 소켓과 클라이언트의 어드레스(IP와 포트번호)를 반환한다.
        self.connected = True # 서버가 클라이언트와 연결된 상태임을 저장한다.
        self.clients[cSock] = {"id" : "", "roomMaster" : None, "noFaceCount" : 0, "eyeBlinkCount" : 0, "otherDirectionCount" : 0}
        # client 인스턴스 변수에 클라이언트 소켓를 키값으로 하여 소켓과 해당 클라이언트에 로그인한 아이디를 저장한다.
        # 지금은 서버로 접속만 했기 때문에 아이디 부분은 빈 부분이다.
        # 아이디 부분 옆은 접속한 방의 방장의 소켓이다. 지금은 아직 방에 들어가지 않았으니 None이다.
        return cSock, cAddr # 클라이언트와 연결된 소켓과 클리이언트의 어드레스 반환
    
    # 접속 종료로 인한 클라이언트 정보 정리
    def disconnect(self, cSock: socket.socket):
        if cSock in self.roomList:
            self.send(cSock, ResDisjoinRoom("", isProfessorOut=True))
        if cSock in self.clients: # 접속을 끊은 클라이언트의 정보가 client 인스턴스 변수에 존재한다면.
            if not self.clients[cSock]["roomMaster"] is None:
                self.send(cSock, ResDisjoinRoom(cSock.getpeername()[0] + " " + str(cSock.getpeername()[1]), isProfessorOut=False))
            del self.clients[cSock] # 클라이언트 정보 삭제
        if len(self.clients) == 0: # 만약 서버에 연결된 클라이언트가 없다면
            self.connected = False # 서버와 연결된 클라이언트가 없는 상태임을 저장한다.
        cSock.close() # 클라이언트와 연결된 소켓을 닫는다.
        print(self.clients)
        print(self.roomList)

    def sendByteData(self, cSock : socket.socket, data : bytearray):
        try:
            cSock.sendall(len(data).to_bytes(4, "little"))
            cSock.sendall(data)
        except Exception as e:
            print(e)

    def sendData(self, cSock : socket.socket, response : Response):
        self.sendByteData(cSock, response.headerBytes)
        for dataByte in response.dataBytesList:
            self.sendByteData(cSock, dataByte)
    
    def send(self, cSock : socket.socket, response : Response):
        if type(response) in [ResRoomList, ResRoomList2, ResLogin, ResSignUp]:
            self.sendData(cSock, response)
        elif type(response) == ResMakeRoom:
            self.sendData(cSock, response)
            if response.isMake:
                for sock in self.clients:
                    self.sendData(sock, ResRoomList2(self.roomList))
        elif type(response) == ResEnterRoom:
            self.sendData(cSock, response)
            if response.isEnter:
                hostSocket = self.clients[cSock]["roomMaster"]
                resJoinRoom = ResJoinRoom(self.db.getName(self.clients[cSock][0]) + "(" + cSock.getpeername()[0] + ")")
                for roomMemberSock in self.roomList[hostSocket]["roomMember"]:
                    self.sendData(roomMemberSock, resJoinRoom)
                self.sendData(hostSocket, resJoinRoom)
        elif ResImage in type(response).mro():
            if response.number == 0:
                for roomMemberSock in self.roomList[cSock]["roomMember"]:
                    self.sendData(roomMemberSock, response)
            elif response.number > 0:
                hostSocket = self.clients[cSock]["roomMaster"]
                self.sendData(hostSocket, response)
        elif type(response) == ResDisjoinRoom:
            if response.isProfessorOut:
                for roomMemberSock in self.roomList[cSock]["roomMember"]:
                    self.clients[roomMemberSock]["roomMaster"] = None
                    self.sendData(roomMemberSock, response)
                del self.roomList[cSock]
                for sock in self.clients:
                    self.sendData(sock, ResRoomList2(self.roomList))
            else:
                hostSocket = self.clients[cSock]["roomMaster"]
                self.clients[cSock]["roomMaster"] = None
                self.roomList[hostSocket]["roomMember"].remove(cSock)
                for roomMemberSock in self.roomList[hostSocket]["roomMember"]:
                    self.sendData(roomMemberSock, response)
                self.sendData(hostSocket, response)
        elif type(response) == ResChat:
            hostSocket = cSock if cSock in self.roomList else self.clients[cSock]["roomMaster"]
            for roomMemberSock in self.roomList[hostSocket]["roomMember"]:
                self.sendData(roomMemberSock, response)
            self.sendData(hostSocket, response)
        
    # 데이터 실제 수신
    def receiveData(self, cSock : socket.socket = None):
        try:
            packet = cSock.recv(4)
            if not packet: # 수신한 데이터가 없으면
                raise # 오류 발생
            dataSize = int.from_bytes(packet, "little")

            receiveBytes = bytearray()
            while len(receiveBytes) < dataSize:
                packetSize = 1024 if len(receiveBytes) + 1024 < dataSize else dataSize - len(receiveBytes)
                packet = cSock.recv(packetSize) # 서버로부터 데이터를 수신받는다.
                if not packet: # 수신한 데이터가 없으면
                    raise # 오류 발생
                receiveBytes.extend(packet)
            return receiveBytes
        except Exception as e:
            self.disconnect(cSock) # 해당 클라이언트의 정보를 해제한다.
            # print(e.with_traceback())
            return None

    def receive(self, cSock : socket.socket = None):
        headerBytes = self.receiveData(cSock)
        if headerBytes is None:
            return (None, None)
        receiveCount = int.from_bytes(headerBytes[0:4], "little")
        dataBytesList = list()
        for i in range(receiveCount):
            receiveBytes = self.receiveData(cSock)
            if receiveBytes is None:
                return (None, None)
            dataBytesList.append(receiveBytes)
        return (headerBytes, dataBytesList)
    
    # 요청 데이터 처리
    # 클라이언트에서 수신받은 요청 데이터의 타입을 구분하여 처리하고
    # 처리된 데이터를 반환하는 함수
    def processData(self, cSock : socket.socket, headerBytes : bytearray, dataBytesList : list[bytearray], 
        mp_face_mesh, face_mesh, mp_drawing, mp_drawing_styles):
    
        request = Request(headerBytes=headerBytes)

        print()
        print(cSock.getpeername())
        print(request.receiveCount)
        print(request.type)
        print(request.totalDataSize)

        receiveTotalSize = 0
        for dataBytes in dataBytesList:
            receiveTotalSize += len(dataBytes)

        print(receiveTotalSize)

        if request.totalDataSize != receiveTotalSize:
            return None

        if request.type == RequestType.image.value: # reqImage
            print("request Image")
            reqImage = ReqImage(request, dataBytesList)
            image = cv2.cvtColor(reqImage.img, cv2.COLOR_BGR2RGB)
            number = -1
            userNum = self.clients[cSock]["id"] #가히
            state = 0
            
            if cSock in self.roomList:
                return ResProImage(image, 0, userNum, state)
            elif not self.clients[cSock]["roomMaster"] is None:
                hostSock = self.clients[cSock]["roomMaster"]
                number = self.roomList[hostSock]["roomMember"].index(cSock) + 1
            
                # To improve performance
                image.flags.writeable = False
                # get the result
                results = face_mesh.process(image)
                # To improve performance
                image.flags.writeable = True

                img_h, img_w, img_c = image.shape

                if results.multi_face_landmarks:
                    face_landmarks = results.multi_face_landmarks[0]
                    
                    mp_drawing.draw_landmarks(
                        image=image,
                        landmark_list=face_landmarks,
                        connections=F.FACEMESH_FACE_OVAL,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=mp_drawing.DrawingSpec(color=(245,117,66), thickness=2)
                        # D.get_default_face_mesh_tesselation_style()
                    )

                    if predictAngle.getPoint(face_landmarks, img_w, img_h):
                        self.clients[cSock]["otherDirectionCount"] += 1
                    else:
                        self.clients[cSock]["otherDirectionCount"] = 0

                    
                    self.clients[cSock]["noFaceCount"] = 0
                    eyeData = predictEye.blinkRatio(image, face_landmarks.landmark, predictEye.LEFT_EYE, predictEye.RIGHT_EYE)
                    predictEyeData = predictEye.model.predict([[eyeData]])[0]
                    if predictEyeData == 'close':
                        self.clients[cSock]["eyeBlinkCount"] += 1
                    else:
                        self.clients[cSock]["eyeBlinkCount"] = 0
                else:
                    self.clients[cSock]["noFaceCount"] += 1
                
                color = (-1, -1, -1)
                if self.clients[cSock]["noFaceCount"] >= 100 and self.clients[cSock]["noFaceCount"] % 10 > 5:
                    color = (255, 0, 0)
                    state = 1
                elif self.clients[cSock]["eyeBlinkCount"] >= 100 and self.clients[cSock]["eyeBlinkCount"] % 10 > 5:
                    color = (0, 255, 0)
                    state = 2
                elif self.clients[cSock]["otherDirectionCount"] >= 100 and self.clients[cSock]["otherDirectionCount"] % 10 > 5:
                    color = (0, 0, 255)
                    state = 3

                if color[0] != -1 and color[1] != -1 and color[2] != -1:
                    image = cv2.line(image, (0, 0), (image.shape[1], 0), color, 20)
                    image = cv2.line(image, (0, 0), (0, image.shape[0]), color, 20)
                    image = cv2.line(image, (image.shape[1], 0), (image.shape[1], image.shape[0]), color, 20)
                    image = cv2.line(image, (0, image.shape[0]), (image.shape[1], image.shape[0]), color, 20)
                
                if number == 1:
                    return ResFirstImage(image, number, userNum, state)
                elif number == 2:
                    return ResSecondImage(image, number, userNum, state)
                elif number == 3:
                    return ResThirdImage(image, number, userNum, state)
                elif number == 4:
                    return ResForthImage(image, number, userNum, state)
        elif request.type == RequestType.roomList.value: # reqRoomList
            print("request Room list")
            return ResRoomList2(self.roomList)
        elif request.type == RequestType.makeRoom.value: # reqMakeRoom
            print("request Make room")
            reqMakeRoom = ReqMakeRoom(request, dataBytesList)
            isMake = False
            if not cSock in self.roomList:
                self.roomList[cSock] = (reqMakeRoom.roomName, [])
                isMake = True
            print(self.roomList)
            return ResMakeRoom(isMake)
        elif request.type == RequestType.enterRoom.value:
            print("request Enter room")
            reqEnterRoom = ReqEnterRoom(request, dataBytesList)
            hostAddress = (reqEnterRoom.ip, reqEnterRoom.port)
            isEnter = False
            for proSock in self.roomList:
                if hostAddress == proSock.getpeername() and cSock.getpeername() != proSock.getpeername() and self.clients[cSock][1] is None and len(self.roomList[proSock][1]) < 1:
                    self.clients[cSock]["roomMaster"] = proSock
                    self.roomList[proSock]["roomMember"].append(cSock)
                    isEnter = True
                    self.clients[cSock]["noFaceCount"] = 0
                    self.clients[cSock]["eyeBlinkCount"] = 0
                    self.clients[cSock]["otherDirectionCount"] = 0
                    break
            return ResEnterRoom(isEnter)
        elif request.type == RequestType.leaveRoom.value:
            print("request leave room")
            isProfessorOut = (True if cSock in self.roomList else False)
            return ResDisjoinRoom(self.db.getName(self.clients[cSock][0]) + "(" + cSock.getpeername()[0] + ")", isProfessorOut=isProfessorOut)
        elif request.type == RequestType.login.value:
            print("request Login")
            reqLogin = ReqLogin(request, dataBytesList)
            isSuccessed, ment = self.db.login(reqLogin.num,reqLogin.pw)
            name = ""
            if isSuccessed:
                self.clients[cSock]["id"] = reqLogin.num
                name = self.db.getName(reqLogin.num)
            return ResLogin(ment=ment,name=name)
        elif request.type == RequestType.signUp.value:
            print("request SignUp")
            reqSignUp = ReqSignUp(request, dataBytesList)
            isSuccessed, ment = self.db.signUp(reqSignUp.name, reqSignUp.num, reqSignUp.pw, reqSignUp.cate)
            return ResSignUp(isSuccessed=isSuccessed, ment=ment)
        #가히
        elif request.type == RequestType.chat.value:
            print("request chat")
            if cSock in self.roomList or not self.clients[cSock]["roomMaster"] is None:
                reqChat = ReqChat(request, dataBytesList)
                print(reqChat.text)
                name = self.db.getName(self.clients[cSock]["id"])
                print(name)
                return ResChat(name + "(" + cSock.getpeername()[0] + ")",reqChat.text)
            