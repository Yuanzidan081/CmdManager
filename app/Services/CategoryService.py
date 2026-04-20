import uuid
from typing import List, Optional

from Domain.AppState import AppState
from Domain.CategoryModel import CategoryModel


class CategoryService:
    def __init__(self, appState: AppState):
        self.appState = appState

    def listCategory(self) -> List[CategoryModel]:
        return sorted(self.appState.categoryList, key=lambda item: item.order)

    def addCategory(self, name: str) -> CategoryModel:
        cleanName = name.strip()
        if not cleanName:
            raise ValueError("分类名称不能为空")

        for category in self.appState.categoryList:
            if category.name.lower() == cleanName.lower():
                raise ValueError("分类名称重复")

        newCategory = CategoryModel(
            id=str(uuid.uuid4()),
            name=cleanName,
            order=len(self.appState.categoryList),
        )
        self.appState.categoryList.append(newCategory)
        self.normalizeOrder()
        self.appState.selectedCategoryId = newCategory.id
        self.appState.hasDirty = True
        return newCategory

    def renameCategory(self, categoryId: str, newName: str) -> None:
        cleanName = newName.strip()
        if not cleanName:
            raise ValueError("分类名称不能为空")

        for category in self.appState.categoryList:
            if category.id != categoryId and category.name.lower() == cleanName.lower():
                raise ValueError("分类名称重复")

        category = self.getCategoryById(categoryId)
        if category is None:
            raise ValueError("分类不存在")

        category.name = cleanName
        self.appState.hasDirty = True

    def removeCategory(self, categoryId: str) -> None:
        category = self.getCategoryById(categoryId)
        if category is None:
            raise ValueError("分类不存在")

        self.appState.categoryList = [
            item for item in self.appState.categoryList if item.id != categoryId
        ]
        self.appState.commandList = [
            item for item in self.appState.commandList if item.categoryId != categoryId
        ]
        self.normalizeOrder()

        if self.appState.selectedCategoryId == categoryId:
            if self.appState.categoryList:
                self.appState.selectedCategoryId = self.listCategory()[0].id
            else:
                self.appState.selectedCategoryId = None

        self.appState.hasDirty = True

    def moveCategory(self, categoryId: str, targetIndex: int) -> None:
        categoryList = self.listCategory()
        currentIndex = -1
        for index, category in enumerate(categoryList):
            if category.id == categoryId:
                currentIndex = index
                break

        if currentIndex < 0:
            raise ValueError("分类不存在")

        if targetIndex < 0 or targetIndex >= len(categoryList):
            raise ValueError("目标位置无效")

        category = categoryList.pop(currentIndex)
        categoryList.insert(targetIndex, category)
        self.appState.categoryList = categoryList
        self.normalizeOrder()
        self.appState.hasDirty = True

    def getCategoryById(self, categoryId: str) -> Optional[CategoryModel]:
        for category in self.appState.categoryList:
            if category.id == categoryId:
                return category
        return None

    def normalizeOrder(self) -> None:
        ordered = self.listCategory()
        for index, category in enumerate(ordered):
            category.order = index
        self.appState.categoryList = ordered
