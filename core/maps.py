"""module holds Map class and all map related functions"""
from dataclasses import dataclass, field
import json
from core.rooms import Room

@dataclass
class Map:
    """a map is a fragment of the gameworld.  It holds"""
    name: str = ''
    uid: str = ''
    rooms: dict[Room] = field(default_factory=dict)

    def initialize(self, path):
        with open(path) as file_handle:
            room_data = json.load(file_handle)
        
            for uid, room in room_data.items():
                self.rooms[uid] = (Room(**room))
