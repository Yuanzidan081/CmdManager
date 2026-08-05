from dataclasses import dataclass


@dataclass
class Workflow:
    id: str
    categoryId: str
    name: str
    description: str
    order: int = 0

    @classmethod
    def fromDict(cls, data: dict) -> "Workflow":
        return cls(str(data.get("id", "")), str(data.get("categoryId", "")), str(data.get("name", "")),
                   str(data.get("description", "")), int(data.get("order", 0)))

    def toDict(self) -> dict:
        return {"id": self.id, "categoryId": self.categoryId, "name": self.name,
                "description": self.description, "order": self.order}