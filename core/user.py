from asyncio.streams import StreamWriter
from dataclasses import dataclass, field

@dataclass
class User:
    """Class which represents a user"""
    socket: StreamWriter = field(default_factory=StreamWriter)
    account_name: str = ''
    remote_address: str = ''
    authorized: bool = False
    current_area: str = ''
    current_room: int = None           # TODO: move this to character at some point

    def __post_init__(self):
        self.current_area = 'test'
        self.current_room = 1

    def is_authorized(self) -> bool:
        """Return True if user's state is currently the authorized state"""
        return self.authorized

    def set_authorized(self, auth: bool) -> None:
        self.authorized = auth
    
def create_user(socket: StreamWriter) -> User:
    """Create barebones unauthorized user and return it"""
    user = User(
        socket=socket,
        account_name='',
        remote_address=socket.get_extra_info('peername'),
        authorized=False
    )

    return user