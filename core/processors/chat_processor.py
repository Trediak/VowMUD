"""Module containing chat processing related classes and functions.

Contained classes and functions process all chat commands sent by user client.  These
commands are parsed to determine which type of chat command was issued and how they should
be handled.
"""
import asyncio
from typing import Tuple
from core.processors.processor_base import ProcessorBase
from core.managers.logger_manager import logger_manager
from core.managers.manager_hub import manager_hub
from core.templates import get_template
from core.user import User

class ChatProcessor(ProcessorBase):
    """Processes all chat commands entered by users.

    Parameters
    ----------
    ProcessorBase : Class
        Abstract base class which ChatProcessor inherits from

    Attributes
    ----------
    shutdown : bool
        Value to track whether processor should be shutdown, default as False
    queue: asyncio.Queue
        Queue which provides work to the processor

    Methods
    -------
    process(user: User, command: str)
        Method which provides interface to add to queue
    run()
        Initialize queue and loop, processing chat commands in queue
    shutdown()
        Initiate shutdown of processor
    """
    def __init__(self):
        self.__shutdown = False
        self.__queue = None

    async def process(self, user: User, command: str) -> None:
        """Interface to add work to processor queue.

        Parameters
        ----------
        user : User
            Instance of User class which is attached as source of chat command to be processed
        command : str
            User input to be processed
        """
        await self.__queue.put((user, command))

    async def run(self) -> int:
        """Start the command processor. Initialize queue and loop, processing commands in queue until shutdown initiated.

        Returns
        -------
        int
            Return code of processor, 0 being the only good return
        """
        # queue must be created here to be in main event loop
        self.__queue = asyncio.Queue()

        # loop until shutdown is issued to instance
        while not self.__shutdown:
            # unpack message from queue
            user, message = await self._consume()

            # separates command to [0] and remainder of message to [2]
            command = message.partition(' ')

            await self._route_chat(user, command[0], command[2])

        # zero is a "good" return code
        return 0

    async def shutdown(self) -> None:
        """Initate shutdown of the chat processor.
        """
        self.__shutdown = True

    async def _consume(self) -> Tuple[User, str]:
        """Consume work from queue.

        Returns
        -------
        Tuple[User, str]
            Tuple containing source and chat command to be processed
        """
        message = await self.__queue.get()

        return message

    async def _route_chat(self, user: User, command: str, payload: str) -> None:
        """Method to abstract the routing of the chat command to correct function

        Parameters
        ----------
        user : User
            Instance of User class which is attached as source of chat command to be processed
        command : str
            Chat command to be route to correct function
        payload : str
            Remainder of chat message which may contain destination user
        """
        if command in ['/gos', '/gossip']:
            await self._gossip(user, payload)
        elif command in ['/tell']:
            await self._tell(user, payload)

    async def _gossip(self, source_user: User, payload: str) -> None:
        """Method to display message from user to the gossip channel.

        Parameters
        ----------
        source_user : User
            Instance of User class which is attached as source of chat command to be processed
        payload : str
            Message to be shown in chat chanel from source user
        """
        # send message to all users
        for _, user in manager_hub.user_manager.users.items():
            if user.account_name == source_user.account_name:
                source_user.socket.write((await get_template('chat', 'gossip') % ('You', '', payload)).encode('ascii'))
                await source_user.socket.drain()
            else:
                user.socket.write((await get_template('chat', 'gossip') % (source_user.account_name, 's', payload)).encode('ascii'))
                await user.socket.drain()

            # log chat information
            await logger_manager.chat.info({'source_user': source_user.account_name, 'destination_user': '', 'channel': 'gossip', 'message': payload})

        # task is complete
        self.__queue.task_done()

    async def _tell(self, source_user: User, payload: str) -> None:
        """Method to display message from source user to only destination user.

        Parameters
        ----------
        source_user : User
            Instance of User class which is attached as source of chat command to be processed
        payload : str
            Message to be shown in chat chanel from source user.  Contains destination user
        """
        # get the destination user name from payload
        destination_account_name, _, message = payload.partition(' ')

        # determine if destination user is online
        if manager_hub.user_manager.is_logged_in(destination_account_name):
            destination_user = manager_hub.user_manager.get_user_by_account_name(destination_account_name)

            # send message to destination user
            destination_user.socket.write((await get_template('chat', 'tell') % (source_user.account_name, 's', 'you', message)).encode('ascii'))
            await destination_user.socket.drain()

            # send message to source user with first persion version
            source_user.socket.write((await get_template('chat', 'tell') % ('You', '', destination_account_name, message)).encode('ascii'))
            await source_user.socket.drain()

            # log chat information
            await logger_manager.chat.info(
                {
                    'source_user': source_user.account_name,
                    'destination_user': destination_account_name,
                    'channel': 'tell',
                    'message': message,
                    'error': ''
                    }
                )
        else:
            # send message to source user that destination is not logged in
            source_user.socket.write((await get_template('system', 'not_logged_in') % destination_account_name).encode('ascii'))
            await source_user.socket.drain()

            # log chat information
            await logger_manager.chat.info(
                {
                    'source_user': source_user.account_name,
                    'destination_user': destination_account_name,
                    'channel': 'tell',
                    'message': message,
                    'error': 'User not logged in.'
                    }
                )

        # task is complete
        self.__queue.task_done()

# Create instance of ChatProcessor in module namespace
chat_processor = ChatProcessor()
