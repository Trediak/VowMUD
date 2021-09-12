"""Module containing command process related classes and functions.

Contained classes and functions process all commands sent by user client.  These
commands are parsed to determine which processor should process the command.  Once
parsed, command is pushed to the correct processor.
"""
import asyncio
from typing import Tuple
from core.processors.processor_base import ProcessorBase
from core.processors.chat_processor import chat_processor
from core.templates import get_template
from core.user import User

class CommandProcessor(ProcessorBase):
    """Processes all commands entered by users and pushes to the correct processor.

    Parameters
    ----------
    ProcessorBase : Class
        Abstract base class which CommandProcessor inherits from

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
        Initialize queue and loop, processing commands in queue
    shutdown()
        Initiate shutdown of processor
    """
    def __init__(self):
        self.__shutdown = False
        self.__queue = None

    async def process(self, user: User, command: str) -> None:
        """Interface to add work to processor queue

        Parameters
        ----------
        user : User
            Instance of User class which is attached as source of command to be processed
        command : str
            User input to be processed as command
        """
        await self.__queue.put((user, command))

    async def run(self) -> int:
        """Start the command processor. Initialize queue and loop, processing commands in queue until shutdown initiated

        Returns
        -------
        int
            Return code of processor, 0 being the only good return
        """
        # queue must be created here to be in main event loop
        self.__queue = asyncio.Queue()

        # loop until shutdown is issued to instance
        while not self.__shutdown:
            user, message = await self._consume()

            command = message.partition(' ')[0]

            # TODO: test for keys existence, otherwise, send user command does not exist
            if command not in _command_map:
                user.socket.write((await get_template('system', 'invalid_command') % command).encode('ascii'))
                await user.socket.drain()

                continue

            await _command_map[command].process(user, message)

            self.__queue.task_done()

        # zero is a "good" return code
        return 0

    async def shutdown(self) -> None:
        """Initate shutdown of the command processor
        """
        self.__shutdown = True

    async def _consume(self) -> Tuple[User, str]:
        """Consume work from queue

        Returns
        -------
        Tuple[User, str]
            Tuple containing source and command to be processed
        """
        message = await self.__queue.get()

        return message

# define the command mapping from command (or shortcut) to processor
_command_map = {
    '/gos': chat_processor,
    '/gossip': chat_processor,
    '/tell': chat_processor,
}

# Create instance of CommandProcessor in module namespace
command_processor = CommandProcessor()
