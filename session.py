import uuid
import enum

class DraftSession(object):
    def __init__(self) -> None:
        self.session_id = uuid.uuid4()
