import uuid
from typing import List, Optional

from Base.JsonBase import JsonBase
from Base.TerminalBase import TerminalBase
from Domain.AppState import AppState
from Domain.CategoryModel import CategoryModel
from Domain.CommandModel import CommandModel
from Domain.SegmentModel import SegmentModel


class CommandService:
    def __init__(
        self,
        appState: AppState,
        jsonBase: JsonBase,
        terminalBase: TerminalBase,
        dataFilePath: str,
    ):
        self.appState = appState
        self.jsonBase = jsonBase
        self.terminalBase = terminalBase
        self.dataFilePath = dataFilePath

    def loadAll(self) -> None:
        jsonData = self.jsonBase.loadFromFile(self.dataFilePath)

        categoryList: List[CategoryModel] = []
        for categoryData in jsonData.get("categories", []):
            categoryList.append(CategoryModel.fromDict(categoryData))
        categoryList = sorted(categoryList, key=lambda item: item.order)
        for index, category in enumerate(categoryList):
            category.order = index

        commandList: List[CommandModel] = []
        for commandData in jsonData.get("commands", []):
            commandList.append(CommandModel.fromDict(commandData))

        self.appState.categoryList = categoryList
        self.appState.commandList = commandList

        if categoryList:
            validSelected = False
            for category in categoryList:
                if category.id == self.appState.selectedCategoryId:
                    validSelected = True
                    break
            if not validSelected:
                self.appState.selectedCategoryId = categoryList[0].id
        else:
            self.appState.selectedCategoryId = None

        self.appState.hasDirty = False

    def saveAll(self) -> None:
        categoryList = sorted(self.appState.categoryList, key=lambda item: item.order)
        commandList = list(self.appState.commandList)
        for category in categoryList:
            self.normalizeCommandOrder(category.id)

        jsonData = {
            "categories": [category.toDict() for category in categoryList],
            "commands": [command.toDict() for command in self.appState.commandList],
        }
        self.jsonBase.saveToFile(self.dataFilePath, jsonData)
        self.appState.hasDirty = False

    def addCommand(
        self,
        categoryId: str,
        name: str,
        description: str,
        segments: list[SegmentModel],
    ) -> CommandModel:
        cleanName = name.strip()
        if not cleanName:
            raise ValueError("命令名称不能为空")
        if not segments:
            raise ValueError("至少需要一个命令片段")

        categoryExists = False
        for category in self.appState.categoryList:
            if category.id == categoryId:
                categoryExists = True
                break
        if not categoryExists:
            raise ValueError("分类不存在")

        commandOrder = self.countCommandInCategory(categoryId)
        newCommand = CommandModel(
            id=str(uuid.uuid4()),
            categoryId=categoryId,
            name=cleanName,
            description=description.strip(),
            segments=segments,
            order=commandOrder,
        )
        self.appState.commandList.append(newCommand)
        self.normalizeCommandOrder(categoryId)
        self.appState.hasDirty = True
        return newCommand

    def updateCommand(
        self,
        commandId: str,
        name: str,
        description: str,
        segments: list[SegmentModel],
    ) -> None:
        command = self.getCommandById(commandId)
        if command is None:
            raise ValueError("命令不存在")
        cleanName = name.strip()
        if not cleanName:
            raise ValueError("命令名称不能为空")
        if not segments:
            raise ValueError("至少需要一个命令片段")

        command.name = cleanName
        command.description = description.strip()
        command.segments = segments
        self.appState.hasDirty = True

    def removeCommand(self, commandId: str) -> None:
        command = self.getCommandById(commandId)
        if command is None:
            raise ValueError("命令不存在")

        categoryId = command.categoryId
        self.appState.commandList = [
            item for item in self.appState.commandList if item.id != commandId
        ]
        self.normalizeCommandOrder(categoryId)
        self.appState.hasDirty = True

    def moveCommand(self, categoryId: str, commandId: str, targetIndex: int) -> None:
        commandList = self.listCommand(categoryId)
        currentIndex = -1
        for index, command in enumerate(commandList):
            if command.id == commandId:
                currentIndex = index
                break

        if currentIndex < 0:
            raise ValueError("命令不存在")
        if targetIndex < 0 or targetIndex >= len(commandList):
            raise ValueError("目标位置无效")

        command = commandList.pop(currentIndex)
        commandList.insert(targetIndex, command)

        otherCommandList = [
            item for item in self.appState.commandList if item.categoryId != categoryId
        ]
        for index, item in enumerate(commandList):
            item.order = index
        self.appState.commandList = otherCommandList + commandList
        self.appState.hasDirty = True

    def listCommand(self, categoryId: str) -> list[CommandModel]:
        categoryCommandList = [
            item for item in self.appState.commandList if item.categoryId == categoryId
        ]
        return sorted(categoryCommandList, key=lambda item: item.order)

    def countCommandInCategory(self, categoryId: str) -> int:
        count = 0
        for command in self.appState.commandList:
            if command.categoryId == categoryId:
                count += 1
        return count

    def getCommandById(self, commandId: str) -> Optional[CommandModel]:
        for command in self.appState.commandList:
            if command.id == commandId:
                return command
        return None

    def buildCommandPreview(self, segments: list[SegmentModel]) -> str:
        tokenList: list[str] = []
        for segment in segments:
            rawValue = segment.value.strip()
            if not rawValue:
                continue
            tokenList.append(self.quoteIfNeed(rawValue))
        return " ".join(tokenList)

    def runCommand(self, commandId: str, terminalType: str = "cmd") -> str:
        command = self.getCommandById(commandId)
        if command is None:
            raise ValueError("命令不存在")

        commandText = self.buildCommandPreview(command.segments)
        if not commandText:
            raise ValueError("命令内容为空")

        self.terminalBase.run(commandText, terminalType)
        return commandText

    def quoteIfNeed(self, rawValue: str) -> str:
        cleanValue = rawValue.strip()
        if not cleanValue:
            return ""

        # 兼容历史数据中写成 \"value\" 的情况。
        if len(cleanValue) >= 4 and cleanValue[:2] == '\\"' and cleanValue[-2:] == '\\"':
            cleanValue = cleanValue[2:-2].strip()
            if not cleanValue:
                return '""'

        # 将用户手动包裹的一层双引号视为参数包裹，而非字面字符。
        if len(cleanValue) >= 2 and cleanValue[0] == '"' and cleanValue[-1] == '"':
            cleanValue = cleanValue[1:-1].strip()
            if not cleanValue:
                return '""'

        hasSpace = (" " in cleanValue) or ("\t" in cleanValue)
        if not hasSpace:
            return cleanValue

        escaped = cleanValue.replace('"', '""')
        return f'"{escaped}"'

    def normalizeCommandOrder(self, categoryId: str) -> None:
        categoryCommandList = self.listCommand(categoryId)
        for index, command in enumerate(categoryCommandList):
            command.order = index
