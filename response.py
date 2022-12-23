from enum import Enum

class ResponseType(Enum):
    Chat = 1

class Response:
    def __init__(self):
        self.headerBytes = bytearray()
        self.dataBytes = bytearray()
    
    def totalBytes(self):
        totalDataBytes = bytearray()
        totalDataBytes.extend(len(self.headerBytes).to_bytes(4, "little"))
        totalDataBytes.extend(self.headerBytes)
        totalDataBytes.extend(self.dataBytes)
        return totalDataBytes
    
    def extendBytes(self, data : bytearray):
        self.headerBytes.extend(len(data).to_bytes(4, "little"))
        self.dataBytes.extend(data)

class ResChat(Response):
    def __init__(self, msg : str):
        super().__init__()
        self.headerBytes.extend(ResponseType.Chat.value.to_bytes(4, "little"))
        self.extendBytes(msg.encode())



        