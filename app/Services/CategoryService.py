import uuid
from typing import List, Optional

from Domain.AppState import AppState
from Domain.CategoryModel import CategoryModel


class CategoryService:
    def __init__(self, appState: AppState): self.appState = appState
    def listCategory(self) -> List[CategoryModel]: return sorted(self.appState.categoryList, key=lambda item: item.order)
    def addCategory(self, name: str) -> CategoryModel:
        name = name.strip()
        if not name: raise ValueError("分类名称不能为空")
        if any(item.name.lower() == name.lower() for item in self.appState.categoryList): raise ValueError("分类名称重复")
        item = CategoryModel(str(uuid.uuid4()), name, len(self.appState.categoryList))
        self.appState.categoryList.append(item); self.appState.selectedCategoryId = item.id; self.appState.hasDirty = True; return item
    def renameCategory(self, categoryId: str, newName: str) -> None:
        item = self.getCategoryById(categoryId); newName = newName.strip()
        if item is None: raise ValueError("分类不存在")
        if not newName: raise ValueError("分类名称不能为空")
        if any(x.id != categoryId and x.name.lower() == newName.lower() for x in self.appState.categoryList): raise ValueError("分类名称重复")
        item.name = newName; self.appState.hasDirty = True
    def removeCategory(self, categoryId: str) -> None:
        if self.getCategoryById(categoryId) is None: raise ValueError("分类不存在")
        templateIds = {x.id for x in self.appState.templateList if x.categoryId == categoryId}
        workflowIds = {x.id for x in self.appState.workflowList if x.categoryId == categoryId}
        self.appState.categoryList = [x for x in self.appState.categoryList if x.id != categoryId]
        self.appState.templateList = [x for x in self.appState.templateList if x.id not in templateIds]
        self.appState.workflowList = [x for x in self.appState.workflowList if x.id not in workflowIds]
        self.appState.instanceList = [x for x in self.appState.instanceList if x.templateId not in templateIds]
        for index, item in enumerate(self.listCategory()): item.order = index
        self.appState.selectedCategoryId = self.appState.categoryList[0].id if self.appState.categoryList else None
        self.appState.hasDirty = True
    def getCategoryById(self, categoryId: str) -> Optional[CategoryModel]: return next((x for x in self.appState.categoryList if x.id == categoryId), None)