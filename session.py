import uuid
import enum
from discord import *
import errors

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

    # def get_state() -> str:
    #     return self.state[11:].lower()

    def check_captains(self) -> bool:
        return self.captain1 and self.captain2

    def advance_state(self) -> bool:
        if self.state == DraftState.FIRST_BAN:
            self.state = DraftState.FIRST_PICK
            return True
        elif self.state == DraftState.FIRST_PICK:
            self.state = DraftState.SECOND_PICK
            return True
        elif self.state == DraftState.SECOND_PICK:
            self.state = DraftState.SECOND_BAN
            return True
        elif self.state == DraftState.SECOND_BAN:
            self.state = DraftState.THIRD_PICK
            return True
        elif self.state == DraftState.THIRD_PICK:
            self.state = DraftState.COMPLETE
            return True
        return False

    def check_state(self) -> bool:
        return self.check_captains() and \
                self.captain1.id in self.picks[self.state].keys() and \
                self.captain2.id in self.picks[self.state].keys()

    def pick(self, captain_id: int, champ: str) -> None:
        clean = champ.lower().strip()
        enemy_captain_id = self.captain1.id if self.captain1.id != captain_id else self.captain2.id

        picks = []
        bans = []
        enemy_picks = []
        enemy_bans = []

        pick_states = [DraftState.FIRST_PICK, DraftState.SECOND_PICK, DraftState.THIRD_PICK]
        ban_states = [DraftState.FIRST_BAN, DraftState.SECOND_BAN]

        for pick_state in pick_states:
            if captain_id in self.picks[pick_state].keys():
                picks.append(self.picks[pick_state][captain_id])
            if enemy_captain_id in self.picks[pick_state].keys():
                enemy_picks.append(self.picks[pick_state][enemy_captain_id])

        for ban_state in ban_states:
            if captain_id in self.picks[ban_state].keys():
                bans.append(self.picks[ban_state][captain_id])
            if enemy_captain_id in self.picks[ban_state].keys():
                enemy_bans.append(self.picks[ban_state][enemy_captain_id])

        print(picks, bans, enemy_picks, enemy_bans, sep='\n')

        if clean not in CHAMP_LIST:
            raise NonexistantChampion("Nonexistant Champion")

        if self.state == DraftState.FIRST_PICK and clean in enemy_bans:
            raise BannedChampion("Banned Champion")

        if self.state == DraftState.SECOND_PICK and clean in enemy_bans:
            raise BannedChampion("Banned Champion")

        if self.state == DraftState.SECOND_PICK and clean in picks:
            raise DuplicateChampion("Duplicate Champion")

        if self.state == DraftState.SECOND_BAN and clean in bans:
            raise DuplicateBan("Duplicate Ban")

        if self.state == DraftState.SECOND_BAN and clean in enemy_picks:
            raise LateBan("Champion Already Picked")

        if self.state == DraftState.THIRD_PICK and clean in enemy_bans:
            raise BannedChampion("Banned Champion")

        if self.state == DraftState.THIRD_PICK and clean in picks:
            raise DuplicateChampion("Duplicate Champion")

        self.picks[self.state][captain_id] = clean
