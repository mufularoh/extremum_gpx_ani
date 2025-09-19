import enum

class MessageType(enum.Enum):
    Success = enum.auto()
    Error = enum.auto()
    Info = enum.auto()

def debug_output(message: str, message_type: MessageType):
    colors: dict[MessageType, str] = {
        MessageType.Error: "\033[91m",
        MessageType.Success: "\033[92m",
        MessageType.Info: "\033[96m"
    }
    endc = "\033[0m"
    print(f"{colors[message_type]}{message}{endc}")
