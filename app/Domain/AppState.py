from dataclasses import dataclass, field
from typing import List, Optional

from Domain.CategoryModel import CategoryModel
from Domain.CommandInstance import CommandInstance
from Domain.CommandTemplate import CommandTemplate
from Domain.GlobalVariableModel import GlobalVariableModel
from Domain.Workflow import Workflow


@dataclass
class AppState:
    categoryList: List[CategoryModel] = field(default_factory=list)
    templateList: List[CommandTemplate] = field(default_factory=list)
    instanceList: List[CommandInstance] = field(default_factory=list)
    workflowList: List[Workflow] = field(default_factory=list)
    globalVariableList: List[GlobalVariableModel] = field(default_factory=list)
    selectedCategoryId: Optional[str] = None
    isSettingsPage: bool = False
    hasDirty: bool = False