"""Module holds Map class and all map related functions.
"""
from dataclasses import dataclass, field
import aiosqlite

@dataclass
class RoomExit:
    """Class which holds room exit information.
    """
    exit_text: str = ''
    exit_type: str = ''
    connecting_area: str = ''
    connecting_room: int = None
    active: bool = True

@dataclass
class Room:
    """Class which holds room information.
    """
    name: str = ""
    description: str = ""
    exits: dict[int, RoomExit] = field(default_factory=dict)
    switches: str = ""
    contents: list = field(default_factory=list)
    occupants: list = field(default_factory=list)

@dataclass
class Area:
    """Class which holds area information
    """
    name: str = ''
    uid: str = ''
    rooms: dict[int, Room] = field(default_factory=dict)

@dataclass
class World:
    """Class which holds World information.

    World heirarchy is World -> Area -> Room

    Attributes
    ----------
    areas : dict[str, Area]
        Dictionary of area names with associated Area instance as value

    Methods
    -------
    load_map_geography()
        Sequentially call steps of populating world information
    get_room_exits(area_name: str, room_number: int)
        Return room exits as dictionary of exit text with instance of RoomExit as value
    get_room_exits_text(area_name: str, room_number: int)
        Return room exits as string

    """
    areas: dict[str, Area] = field(default_factory=dict)

    async def load_map_geography(self) -> None:
        """Sequentially call steps of populating world information
        """
        await self._load_map_by_rooms()
        await self._connect_rooms()

    async def get_room_exits(self, area_name: str, room_number: int) -> dict[str, RoomExit]:
        """Return room exits as dictionary of exit text with instance of RoomExit as value

        Parameters
        ----------
        area_name : str
            Area name
        room_number : int
            Room number

        Returns
        -------
        dict[str, RoomExit]
            Exit text with instance of RoomExit as value
        """
        room_exits = {}

        for connection_text, room_exit in self.areas[area_name].rooms[room_number].exits.items():
            room_exits[connection_text] = room_exit

        return room_exits

    async def get_room_exits_text(self, area_name: str, room_number: int) -> str:
        """Return room exits as string

        Parameters
        ----------
        area_name : str
            Area name
        room_number : int
            Room number

        Returns
        -------
        str
            Room exit keys join as string
        """
        room_exits = []

        for connection_text, _ in self.areas[area_name].rooms[room_number].exits.items():
            room_exits.append(connection_text)

        return ', '.join(room_exits)

    async def _load_map_by_rooms(self) -> None:
        """Load room information from database and place in world under the associated area dictionary.
        """
        query = '''SELECT
                    area_name,
                    room_number,
                    room_name,
                    room_description
                   FROM rooms_general;
                '''

        async with aiosqlite.connect('./db/test.db') as db_conn:
            async with db_conn.execute(query) as cursor:
                async for row in cursor:
                    area_name = row[0]
                    room_number = row[1]

                    if area_name not in self.areas:
                        self.areas[area_name] = Area()

                    if room_number not in self.areas[area_name].rooms:
                        self.areas[area_name].rooms[room_number] = Room(
                            name = row[2],
                            description = row[3]
                        )

    async def _connect_rooms(self) -> None:
        """Load room connection information from database updating rooms under the associated area dictionaries.
        """
        query = '''SELECT
                    area_name,
                    room_number,
                    exit_text,
                    exit_type,
                    connecting_area,
                    connecting_room,
                    active
                   FROM rooms_connections;
                '''

        async with aiosqlite.connect('./db/test.db') as db_conn:
            async with db_conn.execute(query) as cursor:
                async for row in cursor:
                    db_area_name = row[0]
                    db_room_number = row[1]
                    db_exit_text = row[2]

                    if db_exit_text not in self.areas[db_area_name].rooms[db_room_number].exits:
                        self.areas[db_area_name].rooms[db_room_number].exits[db_exit_text] = RoomExit(
                            exit_text = db_exit_text,
                            exit_type = row[3],
                            connecting_area = row[4],
                            connecting_room = row[5],
                            active = row[6]
                        )

# Create instance of World in module namespace
world_map = World()
