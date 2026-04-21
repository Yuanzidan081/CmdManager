from dataclasses import dataclass


@dataclass
class SegmentModel:
    key: str
    value: str

    @classmethod
    def fromDict(cls, data: dict) -> "SegmentModel":
        segmentKey = str(data.get("key", "")).strip()
        segmentValue = str(data.get("value", ""))
        return cls(key=segmentKey, value=segmentValue)

    def toDict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
        }
