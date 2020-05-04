import uuid
import enum
from discord import *
from errors import *
# from prettytable import PrettyTable

CHAMP_LIST = [
    "alysia", "ashka", "bakko", "blossom", "croak", "destiny", "ezmo", "freya", 
    "iva", "jade", "jamila", "jumong", "lucie", "oldur", "pearl", "pestilus", 
    "poloma", "raigon", "rook", "ruh kaan", "shen rao", "shifu", "sirius",
    "taya", "thorn", "ulric", "varesh", "zander",
]
SHORT_CHAMP_DICT = ["dio": "pearl", "ruh": "ruh kaan", "rk": "ruh kaan", "shen": "shen rao"]

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
        self.draft_message_id: int = None
        self.nail_draft: bool = False

        # init table
        self.table = Embed(color = 16753152)
        self.table.add_field(name = "_Captains_", value = "Ban\nPick\nPick\nBan\nPick")
        self.table.add_field(
            name = "**captain 1**",
            value = "----\n----\n----\n----\n----"
        )
        self.table.add_field(
            name = "**captain 2**",
            value = "----\n----\n----\n----\n----"
        )

        # litterally no idea
        for key in DraftState:
            self.picks[key] = {}

    @staticmethod
    def get_short_uuid() -> str:
        return uuid.uuid4().hex[:6]

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

        # print(picks, bans, enemy_picks, enemy_bans, sep='\n')

        if clean in SHORT_CHAMP_DICT:
            clean = SHORT_CHAMP_DICT[clean]

        # checking for pick errors
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

    def update_table(self) -> None:
        champs1 = ["----" for i in range(5)]
        champs2 = ["----" for i in range(5)]

        c1 = 0
        c2 = 0

        for key in DraftState:
            if self.picks[key]:
                champs1[c1] = self.picks[key][self.captain1.id]
                champs2[c2] = self.picks[key][self.captain2.id]
            c1 += 1
            c2 += 1

        self.table.set_field_at(
            index = 1,
            name = "**" + self.captain1.display_name + "**",
            value = "\n".join(champs1)
        )
        self.table.set_field_at(
            index = 2,
            name = "**" + self.captain2.display_name + "**",
            value = "\n".join(champs2)
        )

    def get_champ_picks(self) -> list:
        champs = []

        for key in DraftState:
            if self.picks[key]:
                champs.append(self.picks[key][self.captain1.id])
                champs.append(self.picks[key][self.captain2.id])

        champs[2], champs[6] = champs[6], champs[2]
        champs[3], champs[7] = champs[7], champs[3]

        return champs
