from dataclasses import dataclass, field
from typing import List

from Domain.VariableValue import VariableValue


@dataclass
class CommandTemplate:
    id: str
    categoryId: str
    name: str
    description: str
    template: str
    defaultVariables: List[VariableValue] = field(default_factory=list)
    revision: int = 1

    @classmethod
    def fromDict(cls, data: dict) -> "CommandTemplate":
        return cls(
            id=str(data.get("id", "")), categoryId=str(data.get("categoryId", "")),
            name=str(data.get("name", "")), description=str(data.get("description", "")),
            template=str(data.get("template", "")),
            defaultVariables=[VariableValue.fromDict(item) for item in data.get("defaultVariables", [])],
            revision=max(1, int(data.get("revision", 1))),
        )

    def toDict(self) -> dict:
        return {"id": self.id, "categoryId": self.categoryId, "name": self.name,
                "description": self.description, "template": self.template,
                "defaultVariables": [item.toDict() for item in self.defaultVariables],
                "revision": self.revision}