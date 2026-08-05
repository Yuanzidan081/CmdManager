from dataclasses import dataclass


@dataclass
class VariableValue:
    key: str
    value: str = ""

    @classmethod
    def fromDict(cls, data: dict) -> "VariableValue":
        return cls(key=str(data.get("key", "")).strip(), value=str(data.get("value", "")))

    def toDict(self) -> dict:
        return {"key": self.key, "value": self.value}