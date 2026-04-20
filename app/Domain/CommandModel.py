from dataclasses import dataclass, field
from typing import List

from Domain.SegmentModel import SegmentModel


@dataclass
class CommandModel:
    id: str
    categoryId: str
    name: str
    description: str
    segments: List[SegmentModel] = field(default_factory=list)
    order: int = 0

    @classmethod
    def fromDict(cls, data: dict) -> "CommandModel":
        segmentDataList = data.get("segments", [])
        segmentList: List[SegmentModel] = []
        for segmentData in segmentDataList:
            segmentList.append(SegmentModel.fromDict(segmentData))

        commandId = str(data.get("id", ""))
        categoryId = str(data.get("categoryId", ""))
        commandName = str(data.get("name", ""))
        commandDescription = str(data.get("description", ""))
        commandOrder = int(data.get("order", 0))
        return cls(
            id=commandId,
            categoryId=categoryId,
            name=commandName,
            description=commandDescription,
            segments=segmentList,
            order=commandOrder,
        )

    def toDict(self) -> dict:
        return {
            "id": self.id,
            "categoryId": self.categoryId,
            "name": self.name,
            "description": self.description,
            "segments": [segment.toDict() for segment in self.segments],
            "order": self.order,
        }
