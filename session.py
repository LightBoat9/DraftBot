import uuid
import enum
from discord import *

CHAMP_LIST = [
    "alysia", "ashka", "bakko", "blossom", "croak", "destiny", "ezmo", "freya", 
    "iva", "jade", "jamila", "jumong", "lucie", "oldur", "pearl", "pestilus", 
    "poloma", "raigon", "rook", "ruh kaan", "shen rao", "shifu", "sirius",
    "taya", "thorn", "ulric", "varesh", "zander",
]

unique_ids = []

class DraftState(Enum):
    FIRST_BAN = 0
    FIRST_PICK = 1
    SECOND_PICK = 2
    SECOND_BAN = 3
    THIRD_PICK = 4
    COMPLETE = 5

class DraftSession():
    def __init__(self) -> None:
        self.session_id = DraftSession.get_short_uuid()

        # Regernate until the id is unique
        while self.session_id in unique_ids:
            self.session_id = DraftSession.get_short_uuid()

        unique_ids.append(self.session_id)

        self.state = DraftState.FIRST_BAN
        self.captain1: User = None
        self.captain2: User = None
        self.picks: dict = {}

        for key in DraftState:
            self.picks[key] = {}

    @staticmethod
    def get_short_uuid() -> str:
        return uuid.uuid4().hex[:6]

    def get_state() -> str:
        return self.state[11:].lower()

    def check_captains(self) -> bool:
        return self.captain1 and self.captain2

    def check_state(self) -> bool:
        return self.check_captains() and \
                self.captain1.id in self.picks[self.state].keys() \
                and self.captain2.id in self.picks[self.state].keys()

    def pick(self, captain_id: int, champ: str) -> bool:
        clean = champ.lower().strip()

        if clean not in CHAMP_LIST:
            raise ValueError("Unknown Champion")

        self.picks[self.state][captain_id] = clean

        if self.check_state():
            if self.state == DraftState.FIRST_BAN:
                self.state = DraftState.FIRST_PICK
            elif self.state == DraftState.FIRST_PICK:
                self.state = DraftState.SECOND_PICK
            elif self.state == DraftState.SECOND_PICK:
                self.state = DraftState.SECOND_BAN
            elif self.state == DraftState.SECOND_BAN:
                self.state = DraftState.THIRD_PICK
