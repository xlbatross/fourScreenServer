from enum import Enum
from request import *

class ResponseType(Enum):
    # tcp
    Chat = 0
    # udp
    FirstImage = 1
    SecondImage = 2
    ThirdImage = 3
    FourthImage = 4

class Response:
    def __init__(self):
        self.dataBytesList : list[bytearray] = []
        self.headerBytes : bytearray =  bytearray()
        self.dataBytes : bytearray = bytearray()

class ResponseTCP(Response):
    def __init__(self):
        super().__init__()
    
    def packaging(self, typeValue : int):
        headerList : list[int] = []

        # 헤더
        # 헤더의 길이(4바이트 정수형, 이 길이값은 이 뒤에 오는 데이터의 길이를 의미한다.)
        # + 요청 타입(4바이트 정수형) + 데이터 하나의 바이트 길이(4바이트 정수형) * ((헤더의 길이 / 4바이트) - 1)
        headerList.append(typeValue)
        for db in self.dataBytesList:
            headerList.append(len(db)) # 데이터 하나의 바이트 길이
            self.dataBytes.extend(db) # 데이터 하나
        
        # 헤더의 길이
        self.headerBytes.extend((len(headerList) * 4).to_bytes(4, "little"))
        # 요청 타입 + 데이터 하나의 바이트 길이
        for i in headerList:
            self.headerBytes.extend(i.to_bytes(4, "little"))
    
    def totalSizeByte(self) -> bytes:
        return (len(self.headerBytes) + len(self.dataBytes)).to_bytes(4, "little")

class ResChat(ResponseTCP):
    def __init__(self, msg : str):
        super().__init__()
        self.dataBytesList.append(msg.encode())
        self.packaging(ResponseType.Chat.value)

class ResponseUDP(Response):
    def __init__(self):
        super().__init__()
    
    def packaging(self, typeValue : int, seqNum : int):
        self.headerBytes.extend(typeValue.to_bytes(4, "little"))
        self.headerBytes.extend(seqNum.to_bytes(4, "little"))
        self.dataBytes.extend(self.dataBytesList[0])
    

class ResImage(ResponseUDP):
    def __init__(self, reqUdp : RequestUDP):
        super().__init__()
        self.dataBytesList.append(reqUdp.dataBytesList[0])
        self.packaging(ResponseType.FirstImage.value, reqUdp.seqNum)




        