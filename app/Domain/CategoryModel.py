from dataclasses import dataclass


@dataclass
class CategoryModel:
    id: str
    name: str
    order: int = 0

    @classmethod
    def fromDict(cls, data: dict) -> "CategoryModel":
        categoryId = str(data.get("id", ""))
        categoryName = str(data.get("name", ""))
        categoryOrder = int(data.get("order", 0))
        return cls(id=categoryId, name=categoryName, order=categoryOrder)

    def toDict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "order": self.order,
        }
