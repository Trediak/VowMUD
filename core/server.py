import asyncio
from core.authorization import AuthStateMachine, UserAuthPackage
from core.managers.logger_manager import logger_manager
from core.managers.manager_hub import manager_hub
from core.processors.command_processor import command_processor
from core.user import create_user, User

# async def start_server(manager_hub: ManagerHub) -> None:
async def start_server() -> None:
    server = await asyncio.start_server(handle_connection, '127.0.0.1', 8888)

    # print(f'Serving on {server.sockets[0].getsockname()}')

    async with server:
        await server.serve_forever()

# async def handle_connection(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, manager_hub: ManagerHub) -> None:
async def handle_connection(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    # log message that we are handling connection from "x" address
    print(f'connection initiated from: {writer.get_extra_info("peername")}')

    # create barebones unauthorized user to be registered
    user = create_user(writer)

    # register the user in user manager
    print(f'registering user: {user.account_name}')
    manager_hub.user_manager.register(user)

    # create authorization state machine and push user to authorization process
    authorization_process = AuthStateMachine()
    authorization_process.setup()

    await authorization_process.run(UserAuthPackage(user, reader))

    # if user is authorized enter the main input read loop
    if user.is_authorized():
        user_input = None

        # loop forever or until connection is detected as disconnected or closed by server
        while user_input != b'':
            user_input = await reader.read(100)

            if user_input:
                await command_processor.process(user, user_input.decode().rstrip())

    # log and close connection, unregister user if not authorized or connection lost
    print(f'closing connection from: {user.remote_address}')
    writer.close()

    # unregister the user from user_manager
    print(f'unregistering user: {user.account_name}')
    manager_hub.user_manager.unregister(user)
