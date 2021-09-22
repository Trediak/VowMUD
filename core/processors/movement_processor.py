"""Module containing movement processing related classes and functions.

Contained classes and functions process all movement commands sent by user client.  These
commands are parsed to determine which type of movement command was issued and how they should
be handled.
"""
import asyncio
from typing import Tuple
from core.processors.processor_base import ProcessorBase
from core.managers.logger_manager import logger_manager
from core.templates import get_template
from core.user import User
from core.world import world_map

class MovementProcessor(ProcessorBase):
    """Processes all movement commands entered by users.

    Parameters
    ----------
    ProcessorBase : Class
        Abstract base class which MovementProcessor inherits from

    Attributes
    ----------
    shutdown : bool
        Value to track whether processor should be shutdown, default as False
    queue: asyncio.Queue
        Queue which provides work to the processor
    directions: dict[str, str]
        Keys of valid "directions" and conversion to common direction to ease processing

    Methods
    -------
    process(user: User, command: str)
        Method which provides interface to add to queue
    run()
        Initialize queue and loop, processing movement commands in queue
    shutdown()
        Initiate shutdown of processor
    """
    def __init__(self):
        self.__shutdown = False
        self.__queue = None
        self.directions = {
            'n': 'n',
            'north': 'n',
            's': 's',
            'south': 's',
            'e': 'e',
            'east': 'e',
            'w': 'w',
            'west': 'w',
            'nw': 'nw',
            'northwest': 'nw',
            'ne': 'ne',
            'northeast': 'ne',
            'se': 'se',
            'southeast': 'se',
            'sw': 'sw',
            'southwest': 'sw'
        }

    async def process(self, user: User, command: str) -> None:
        """Interface to add work to movement processor queue.

        Parameters
        ----------
        user : User
            Instance of User class which is attached as source of movement command to be processed
        command : str
            User input to be processed
        """
        await self.__queue.put((user, command))

    async def run(self) -> int:
        """Start the movement processor. Initialize queue and loop, processing commands in queue until shutdown initiated.

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

            # separates command from remainder of message
            command, _, payload = message.partition(' ')

            await self._route_movement(user, command, payload)

        # zero is a "good" return code
        return 0

    async def shutdown(self) -> None:
        """Initate shutdown of the movement processor.
        """
        self.__shutdown = True

    async def _consume(self) -> Tuple[User, str]:
        """Consume work from queue.

        Returns
        -------
        Tuple[User, str]
            Tuple containing source and movement command to be processed
        """
        message = await self.__queue.get()

        return message

    async def _route_movement(self, user: User, command: str, payload: str) -> None:
        """Method to abstract the routing of the movement command to correct function

        Parameters
        ----------
        user : User
            Instance of User class which is attached as source of movement command to be processed
        command : str
            Movement command to be routed to correct function
        payload : str
            Remainder of movement message
        """
        if command.lower() in self.directions:
            await self._move_character(user, command, payload)
        elif command.lower() in ['l', 'look']:
            await self._look(user, payload)

    async def _look(self, user: User, payload: str) -> None:
        """Method allowing user to look into a connected room displaying its details.

        Parameters
        ----------
        user : User
            Instance of User class which is attached as source of movement command to be processed
        payload : str
            Remainder of movement message
        """
        # separates command from remainder of message
        direction, _, excess = payload.partition(' ')

        # send message to user that movement does not exist if direction is not valid
        # or there is excess text
        if direction.lower() not in self.directions or excess:
            user.socket.write((await get_template('game', 'invalid_direction') % (f'{direction} {excess}')).encode('ascii'))
            await user.socket.drain()

            # task is complete
            self.__queue.task_done()

            return

        # get exits of room user is currently in
        room_exits = await world_map.get_room_exits(user.current_area, user.current_room)

        # iterate through room exits.  Convert both to lowercase for comparison
        for exit_direction, room_exit in room_exits.items():
            if self.directions[direction.lower()] == self.directions[exit_direction.lower()]:
                # send user the room details based on template and exit function
                user.socket.write((await get_template('game', 'room') % (
                    world_map.areas[room_exit.connecting_area].rooms[room_exit.connecting_room].name,
                    world_map.areas[room_exit.connecting_area].rooms[room_exit.connecting_room].description,
                    await world_map.get_room_exits_text(room_exit.connecting_area, room_exit.connecting_room),
                    'Wicked Cultist, Ferocious Wolf, Small Baboon'
                )).encode('ascii'))
                await user.socket.drain()

                # task is complete
                self.__queue.task_done()

                return

        # If you reach here, it is valid direction but no matching exit in room
        user.socket.write((await get_template('game', 'no_exit')).encode('ascii'))
        await user.socket.drain()

        # task is complete
        self.__queue.task_done()

    async def _move_character(self, user: User, direction: str, excess: str) -> None:
        """Method to move user to connected room and display its details

        Parameters
        ----------
        user : User
            Instance of User class which is attached as source of movement command to be processed
        direction : str
            Direction command entered by user
        excess : str
            Remainder of movement message
        """
        # send message to user that direction is invalid if excess text
        if excess:
            user.socket.write((await get_template('game', 'invalid_direction') % (f'{direction} {excess}')).encode('ascii'))
            await user.socket.drain()

            # task is complete
            self.__queue.task_done()

            return

        # get exits of room user is currently in
        room_exits = await world_map.get_room_exits(user.current_area, user.current_room)

        # iterate through room exits.  Convert both to lowercase for comparison
        for exit_direction, room_exit in room_exits.items():
            if self.directions[direction.lower()] == self.directions[exit_direction.lower()]:
                # set the characters current_area and current_room to matching exit connecting information
                # TODO: redo some of this after characters are implemented
                user.current_area = room_exit.connecting_area
                user.current_room = room_exit.connecting_room

                # send user updated room display
                user.socket.write((await get_template('game', 'room') % (
                    world_map.areas[user.current_area].rooms[user.current_room].name,
                    world_map.areas[user.current_area].rooms[user.current_room].description,
                    await world_map.get_room_exits_text(user.current_area, user.current_room),
                    'Wicked Cultist, Ferocious Wolf, Small Baboon'
                )).encode('ascii'))
                await user.socket.drain()

                # task is complete
                self.__queue.task_done()

                return

        # If you reach here, it is valid direction but no matching exit in room
        user.socket.write((await get_template('game', 'no_exit')).encode('ascii'))
        await user.socket.drain()

        # task is complete
        self.__queue.task_done()

# Create instance of MovementProcessor in module namespace
movement_processor = MovementProcessor()
