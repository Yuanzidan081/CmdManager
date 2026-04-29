from dataclasses import dataclass, field
from typing import List, Optional

from Domain.CategoryModel import CategoryModel
from Domain.CommandModel import CommandModel
from Domain.GlobalVariableModel import GlobalVariableModel


@dataclass
class AppState:
    categoryList: List[CategoryModel] = field(default_factory=list)
    commandList: List[CommandModel] = field(default_factory=list)
    globalVariableList: List[GlobalVariableModel] = field(default_factory=list)
    selectedCategoryId: Optional[str] = None
    editingCommandId: Optional[str] = None
    isSettingsPage: bool = False
    hasDirty: bool = False
