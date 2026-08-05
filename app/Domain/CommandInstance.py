from dataclasses import dataclass, field
from typing import List, Optional

from Domain.VariableValue import VariableValue


@dataclass
class TemplateSnapshot:
    template: str
    defaultVariables: List[VariableValue] = field(default_factory=list)

    @classmethod
    def fromDict(cls, data: dict) -> "TemplateSnapshot":
        return cls(str(data.get("template", "")), [VariableValue.fromDict(item) for item in data.get("defaultVariables", [])])

    def toDict(self) -> dict:
        return {"template": self.template, "defaultVariables": [item.toDict() for item in self.defaultVariables]}


@dataclass
class CommandInstance:
    id: str
    templateId: str
    workflowId: Optional[str]
    name: str
    order: int
    templateSnapshot: TemplateSnapshot
    templateRevision: int
    variableOverrides: List[VariableValue] = field(default_factory=list)
    pendingVariableKeys: List[str] = field(default_factory=list)

    @classmethod
    def fromDict(cls, data: dict) -> "CommandInstance":
        workflowId = data.get("workflowId")
        return cls(
            id=str(data.get("id", "")), templateId=str(data.get("templateId", "")),
            workflowId=str(workflowId) if workflowId else None, name=str(data.get("name", "")),
            order=int(data.get("order", 0)), templateSnapshot=TemplateSnapshot.fromDict(data.get("templateSnapshot", {})),
            templateRevision=max(1, int(data.get("templateRevision", 1))),
            variableOverrides=[VariableValue.fromDict(item) for item in data.get("variableOverrides", [])],
            pendingVariableKeys=[str(item) for item in data.get("pendingVariableKeys", []) if str(item)],
        )

    def toDict(self) -> dict:
        return {"id": self.id, "templateId": self.templateId, "workflowId": self.workflowId,
                "name": self.name, "order": self.order, "templateSnapshot": self.templateSnapshot.toDict(),
                "templateRevision": self.templateRevision,
                "variableOverrides": [item.toDict() for item in self.variableOverrides],
                "pendingVariableKeys": self.pendingVariableKeys}