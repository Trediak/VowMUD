from dataclasses import dataclass, field

@dataclass
class Room:
    name: str = ""
    description: str = ""
    exits: list[dict] = field(default_factory=list)
    contents: list = field(default_factory=list)
    occupants: list = field(default_factory=list)