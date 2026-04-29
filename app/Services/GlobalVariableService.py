from typing import Optional

from Domain.AppState import AppState
from Domain.GlobalVariableModel import GlobalVariableModel


class GlobalVariableService:
    def __init__(self, appState: AppState):
        self.appState = appState

    def listGlobalVariable(self) -> list[GlobalVariableModel]:
        return list(self.appState.globalVariableList)

    def addGlobalVariable(self, key: str, value: str) -> GlobalVariableModel:
        normalizedKey = self.normalizeKey(key)
        if not normalizedKey:
            raise ValueError("全局变量名不能为空")
        if self.findByKey(normalizedKey) is not None:
            raise ValueError("全局变量名重复")

        item = GlobalVariableModel(
            key=normalizedKey,
            value=value,
        )
        self.appState.globalVariableList.append(item)
        self.appState.hasDirty = True
        return item

    def updateGlobalVariable(self, key: str, value: str) -> None:
        normalizedKey = self.normalizeKey(key)
        item = self.findByKey(normalizedKey)
        if item is None:
            raise ValueError("全局变量不存在")
        item.value = value
        self.appState.hasDirty = True

    def removeGlobalVariable(self, key: str) -> None:
        normalizedKey = self.normalizeKey(key)
        beforeCount = len(self.appState.globalVariableList)
        self.appState.globalVariableList = [
            item for item in self.appState.globalVariableList if item.key != normalizedKey
        ]
        if len(self.appState.globalVariableList) == beforeCount:
            raise ValueError("全局变量不存在")
        self.appState.hasDirty = True

    def searchGlobalVariable(self, keyword: str) -> list[GlobalVariableModel]:
        text = keyword.strip().lower()
        if not text:
            return self.listGlobalVariable()

        matched: list[GlobalVariableModel] = []
        for item in self.appState.globalVariableList:
            if text in item.key.lower() or text in item.value.lower():
                matched.append(item)
        return matched

    def sortGlobalVariable(self, ascending: bool = True) -> list[GlobalVariableModel]:
        return sorted(
            self.appState.globalVariableList,
            key=lambda item: item.key.lower(),
            reverse=not ascending,
        )

    def replaceAll(self, itemList: list[GlobalVariableModel]) -> None:
        keySet: set[str] = set()
        normalizedList: list[GlobalVariableModel] = []

        for item in itemList:
            key = self.normalizeKey(item.key)
            if not key:
                raise ValueError("全局变量名不能为空")
            if key in keySet:
                raise ValueError(f"全局变量名重复：{key}")
            keySet.add(key)
            normalizedList.append(
                GlobalVariableModel(
                    key=key,
                    value=item.value,
                )
            )

        self.appState.globalVariableList = normalizedList
        self.appState.hasDirty = True

    def findByKey(self, key: str) -> Optional[GlobalVariableModel]:
        normalizedKey = self.normalizeKey(key)
        for item in self.appState.globalVariableList:
            if item.key == normalizedKey:
                return item
        return None

    def normalizeKey(self, key: str) -> str:
        return key.strip()
