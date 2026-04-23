from dataclasses import dataclass, field
from typing import List, Optional

from Domain.CategoryModel import CategoryModel
from Domain.CommandModel import CommandModel


@dataclass
class AppState:
    categoryList: List[CategoryModel] = field(default_factory=list)
    commandList: List[CommandModel] = field(default_factory=list)
    selectedCategoryId: Optional[str] = None
    hasDirty: bool = False
