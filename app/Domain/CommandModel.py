from dataclasses import dataclass, field
from typing import List

from Domain.SegmentModel import SegmentModel


@dataclass
class CommandModel:
    id: str
    categoryId: str
    name: str
    description: str
    template: str = ""
    variables: List[SegmentModel] = field(default_factory=list)
    order: int = 0

    @classmethod
    def fromDict(cls, data: dict) -> "CommandModel":
        template = str(data.get("template", "")).strip()

        variableDataList = data.get("variables", [])
        variableList: List[SegmentModel] = []
        for variableData in variableDataList:
            variableList.append(SegmentModel.fromDict(variableData))

        if not template:
            template, variableList = cls.convertLegacySegments(data.get("segments", []))

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
            template=template,
            variables=variableList,
            order=commandOrder,
        )

    @classmethod
    def convertLegacySegments(cls, segmentDataList: list) -> tuple[str, List[SegmentModel]]:
        templatePartList: List[str] = []
        variableList: List[SegmentModel] = []
        variableIndex = 1

        for segmentData in segmentDataList:
            segmentType = str(segmentData.get("type", "literal"))
            segmentValue = str(segmentData.get("value", "")).strip()
            if not segmentValue:
                continue

            if segmentType == "variable":
                variableKey = f"arg{variableIndex}"
                variableIndex += 1
                templatePartList.append(f"%{variableKey}%")
                variableList.append(SegmentModel(key=variableKey, value=segmentValue))
                continue

            templatePartList.append(cls.quoteIfNeed(segmentValue))

        return " ".join(templatePartList), variableList

    @staticmethod
    def quoteIfNeed(rawValue: str) -> str:
        hasSpace = (" " in rawValue) or ("\t" in rawValue)
        if not hasSpace:
            return rawValue

        if len(rawValue) >= 2 and rawValue[0] == '"' and rawValue[-1] == '"':
            return rawValue

        escaped = rawValue.replace('"', '""')
        return f'"{escaped}"'

    def toDict(self) -> dict:
        return {
            "id": self.id,
            "categoryId": self.categoryId,
            "name": self.name,
            "description": self.description,
            "template": self.template,
            "variables": [segment.toDict() for segment in self.variables],
            "order": self.order,
        }
