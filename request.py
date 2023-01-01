from enum import Enum

class RequestType(Enum):
    # tcp
    UDPConnect = 0
    Chat = 1
    # udp
    Image = 2

class Request:
    def __init__(self):
        self.requsetType : int = -1
        self.dataBytesList : list[bytearray] = []

class RequestTCP(Request):
    def __init__(self, rawData : bytearray):
        super().__init__()
        pointer : int = 0
        headerSize : int = 0
        dataLengthList : list[int] = []

        headerSize = int.from_bytes(rawData[pointer : pointer + 4], "little")
        pointer += 4
        self.requsetType = int.from_bytes(rawData[pointer : pointer + 4], "little")
        pointer += 4

        for i in range(0, headerSize - 4, 4):
            dataLengthList.append(int.from_bytes(rawData[pointer : pointer + 4], "little"))
            pointer += 4
        
        for length in dataLengthList:
            self.dataBytesList.append(rawData[pointer : pointer + length])
            pointer += length

class ReqUDPConnect:
    def __init__(self, reqtcp : RequestTCP):
        self.servIp : str = reqtcp.dataBytesList[0].decode()
        self.port : int = int.from_bytes(reqtcp.dataBytesList[1], "little")
    
    def __str__(self):
        return f"servIp : {self.servIp} / port {self.port}"

class RequestUDP(Request):
    def __init__(self, rawData : bytearray):
        super().__init__()
        self.seqNum = -1
        pointer : int = 0

        self.requsetType = int.from_bytes(rawData[pointer : pointer + 4], "little")
        pointer += 4
        self.seqNum = int.from_bytes(rawData[pointer : pointer + 4], "little")
        pointer += 4

        self.dataBytesList.append(rawData[pointer : len(rawData)])

