from dataclasses import dataclass


@dataclass
class Message:
    src: int
    msg: str

    def __dict__(self):
        return {"src": self.src, "msg": self.msg}
