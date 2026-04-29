from dataclasses import dataclass


@dataclass
class GlobalVariableModel:
    key: str
    value: str

    @classmethod
    def fromDict(cls, data: dict) -> "GlobalVariableModel":
        key = str(data.get("key", "")).strip()
        value = str(data.get("value", ""))
        return cls(key=key, value=value)

    def toDict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
        }
