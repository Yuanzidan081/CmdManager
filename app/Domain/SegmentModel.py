from dataclasses import dataclass


@dataclass
class SegmentModel:
    type: str
    value: str

    @classmethod
    def fromDict(cls, data: dict) -> "SegmentModel":
        segmentType = str(data.get("type", "literal"))
        segmentValue = str(data.get("value", ""))
        if segmentType not in {"literal", "variable"}:
            segmentType = "literal"
        return cls(type=segmentType, value=segmentValue)

    def toDict(self) -> dict:
        return {
            "type": self.type,
            "value": self.value,
        }
