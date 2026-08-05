import re
from typing import Callable, Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QDialog,
    QVBoxLayout,
    QWidget,
)

from Domain.CommandModel import CommandModel
from Domain.GlobalVariableModel import GlobalVariableModel
from Domain.SegmentModel import SegmentModel
from UI.widgets.GlobalVarPickerWidget import GlobalVarPickerWidget
from UI.widgets.SegmentWidget import SegmentWidget


class CommandEditorWidget(QWidget):
    saveRequested = pyqtSignal(str, str, str, str, str, list)
    backRequested = pyqtSignal()
    copyPreviewRequested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.currentCommandId = ""
        self.currentCategoryId = ""
        self.previewBuilder: Optional[Callable[[str, list], str]] = None
        self.templateParser: Optional[Callable[[str], list[str]]] = None
        self.globalVariableProvider: Optional[Callable[[], list[GlobalVariableModel]]] = None

        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(10)

        titleLayout = QHBoxLayout()
        self.backButton = QPushButton("返回")
        self.backButton.setObjectName("ghostButton")
        self.titleLabel = QLabel("命令编辑")
        self.titleLabel.setObjectName("pageTitleLabel")
        titleLayout.addWidget(self.backButton)
        titleLayout.addWidget(self.titleLabel)
        titleLayout.addStretch(1)
        mainLayout.addLayout(titleLayout)

        self.editorScrollArea = QScrollArea()
        self.editorScrollArea.setObjectName("editorScrollArea")
        self.editorScrollArea.setWidgetResizable(True)
        self.editorScrollArea.setFrameShape(QFrame.Shape.NoFrame)
        self.editorScrollArea.setFrameShadow(QFrame.Shadow.Plain)
        self.editorScrollArea.setLineWidth(0)
        self.editorScrollArea.setMidLineWidth(0)
        mainLayout.addWidget(self.editorScrollArea, 1)

        self.editorContent = QWidget()
        self.editorLayout = QVBoxLayout(self.editorContent)
        self.editorLayout.setContentsMargins(0, 0, 0, 0)
        self.editorLayout.setSpacing(12)
        self.editorScrollArea.setWidget(self.editorContent)

        baseCard = QFrame()
        baseCard.setObjectName("editorCard")
        baseLayout = QVBoxLayout(baseCard)
        baseLayout.setContentsMargins(14, 14, 14, 14)
        baseLayout.setSpacing(10)

        self.nameEdit = QLineEdit()
        self.nameEdit.setPlaceholderText("命令名称")

        self.descriptionEdit = QTextEdit()
        self.descriptionEdit.setPlaceholderText("命令描述")
        self.descriptionEdit.setFixedHeight(70)

        self.templateEdit = QLineEdit()
        self.templateEdit.setPlaceholderText("命令模板，例如 E:\\unity\\build.bat %appName% %version%")

        self.insertGlobalVariableButton = QPushButton("插入全局变量")
        self.insertGlobalVariableButton.setObjectName("ghostButton")

        templateLayout = QHBoxLayout()
        templateLayout.setContentsMargins(0, 0, 0, 0)
        templateLayout.setSpacing(8)
        templateLayout.addWidget(self.templateEdit, 1)
        templateLayout.addWidget(self.insertGlobalVariableButton, 0)

        baseLayout.addWidget(QLabel("名称"))
        baseLayout.addWidget(self.nameEdit)
        baseLayout.addWidget(QLabel("描述"))
        baseLayout.addWidget(self.descriptionEdit)
        baseLayout.addWidget(QLabel("模板"))
        baseLayout.addLayout(templateLayout)

        self.editorLayout.addWidget(baseCard)

        segmentCard = QFrame()
        segmentCard.setObjectName("editorCard")
        segmentLayout = QVBoxLayout(segmentCard)
        segmentLayout.setContentsMargins(14, 14, 14, 14)
        segmentLayout.setSpacing(10)

        segmentLayout.addWidget(QLabel("变量配置（由模板自动解析）"))

        self.segmentListWidget = QWidget()
        self.segmentListLayout = QVBoxLayout(self.segmentListWidget)
        self.segmentListLayout.setContentsMargins(0, 0, 0, 0)
        self.segmentListLayout.setSpacing(8)
        self.segmentListLayout.addStretch(1)

        segmentLayout.addWidget(self.segmentListWidget)
        self.editorLayout.addWidget(segmentCard)

        previewCard = QFrame()
        previewCard.setObjectName("editorCard")
        previewLayout = QVBoxLayout(previewCard)
        previewLayout.setContentsMargins(14, 14, 14, 14)
        previewLayout.setSpacing(8)
        previewTitleLayout = QHBoxLayout()
        previewTitleLayout.setContentsMargins(0, 0, 0, 0)
        previewTitleLayout.addWidget(QLabel("命令预览"))
        previewTitleLayout.addStretch(1)
        self.copyPreviewButton = QPushButton("复制")
        self.copyPreviewButton.setObjectName("ghostButton")
        self.copyPreviewButton.setEnabled(False)
        previewTitleLayout.addWidget(self.copyPreviewButton)
        previewLayout.addLayout(previewTitleLayout)
        self.previewLabel = QLabel("")
        self.previewLabel.setObjectName("commandPreviewLabel")
        self.previewLabel.setWordWrap(True)
        previewLayout.addWidget(self.previewLabel)

        self.editorLayout.addWidget(previewCard)
        self.editorLayout.addStretch(1)

        self.bottomBar = QWidget()
        self.bottomBar.setObjectName("editorBottomBar")
        bottomLayout = QHBoxLayout(self.bottomBar)
        bottomLayout.setContentsMargins(0, 4, 0, 0)
        bottomLayout.setSpacing(0)
        bottomLayout.addStretch(1)
        self.saveButton = QPushButton("保存")
        self.saveButton.setObjectName("primaryButton")
        bottomLayout.addWidget(self.saveButton)
        mainLayout.addWidget(self.bottomBar)

        self.backButton.clicked.connect(self.backRequested.emit)
        self.nameEdit.textChanged.connect(self.updatePreview)
        self.templateEdit.textChanged.connect(self.onTemplateChanged)
        self.insertGlobalVariableButton.clicked.connect(self.onInsertGlobalVariableClicked)
        self.copyPreviewButton.clicked.connect(self.onCopyPreviewClicked)
        self.saveButton.clicked.connect(self.onSaveClicked)

    def setPreviewBuilder(self, previewBuilder: Callable[[str, list], str]) -> None:
        self.previewBuilder = previewBuilder

    def setTemplateParser(self, templateParser: Callable[[str], list[str]]) -> None:
        self.templateParser = templateParser

    def setGlobalVariableProvider(
        self,
        globalVariableProvider: Callable[[], list[GlobalVariableModel]],
    ) -> None:
        self.globalVariableProvider = globalVariableProvider

    def setNewCommand(self, categoryId: str) -> None:
        self.currentCommandId = ""
        self.currentCategoryId = categoryId
        self.nameEdit.clear()
        self.descriptionEdit.clear()
        self.templateEdit.clear()
        self.syncVariableList([])
        self.updatePreview()

    def loadCommand(self, command: CommandModel) -> None:
        self.currentCommandId = command.id
        self.currentCategoryId = command.categoryId
        self.nameEdit.setText(command.name)
        self.descriptionEdit.setText(command.description)
        self.templateEdit.blockSignals(True)
        self.templateEdit.setText(command.template)
        self.templateEdit.blockSignals(False)
        self.syncVariableList(command.variables)
        self.updatePreview()

    def onTemplateChanged(self) -> None:
        currentVariableList = [SegmentModel.fromDict(item) for item in self.collectVariableData()]
        self.syncVariableList(currentVariableList)
        self.updatePreview()

    def parseTemplateVariableKeys(self, template: str) -> list[str]:
        if self.templateParser is not None:
            return self.templateParser(template)

        keyList: list[str] = []
        keySet: set[str] = set()
        for matched in re.finditer(r"%([^%\s]+)%", template):
            key = matched.group(1).strip()
            if not key:
                continue
            if key in keySet:
                continue
            keySet.add(key)
            keyList.append(key)
        return keyList

    def syncVariableList(self, variableList: list[SegmentModel]) -> None:
        template = self.templateEdit.text()
        keyList = self.parseTemplateVariableKeys(template)

        valueMap: dict[str, str] = {}
        for variable in variableList:
            key = variable.key.strip()
            if not key:
                continue
            if key in valueMap:
                continue
            valueMap[key] = variable.value

        self.clearVariableList()
        for key in keyList:
            self.addVariableInput(key, valueMap.get(key, ""))

    def addVariableInput(self, variableKey: str, variableValue: str) -> None:
        segmentWidget = SegmentWidget(variableKey, variableValue)
        segmentWidget.dataChanged.connect(self.updatePreview)
        self.segmentListLayout.insertWidget(self.segmentListLayout.count() - 1, segmentWidget)

    def clearVariableList(self) -> None:
        while self.segmentListLayout.count() > 1:
            layoutItem = self.segmentListLayout.takeAt(0)
            widget = layoutItem.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

    def collectVariableData(self) -> list[dict]:
        dataList: list[dict] = []
        for index in range(self.segmentListLayout.count() - 1):
            layoutItem = self.segmentListLayout.itemAt(index)
            if layoutItem is None:
                continue
            widget = layoutItem.widget()
            if isinstance(widget, SegmentWidget):
                dataList.append(widget.getData())
        return dataList

    def updatePreview(self) -> None:
        variableDataList = self.collectVariableData()
        variableList = [SegmentModel.fromDict(item) for item in variableDataList]
        template = self.templateEdit.text()
        globalVariableList = []
        if self.globalVariableProvider is not None:
            globalVariableList = self.globalVariableProvider()

        if self.previewBuilder is None:
            preview = template
            for variable in variableList:
                preview = preview.replace(f"%{variable.key}%", variable.value)
        else:
            try:
                preview = self.previewBuilder(template, variableList, globalVariableList)
            except TypeError:
                preview = self.previewBuilder(template, variableList)

        self.previewLabel.setText(preview)
        self.copyPreviewButton.setEnabled(bool(preview.strip()))

    def onCopyPreviewClicked(self) -> None:
        preview = self.previewLabel.text()
        if preview.strip():
            self.copyPreviewRequested.emit(preview)

    def onInsertGlobalVariableClicked(self) -> None:
        if self.globalVariableProvider is None:
            return

        globalVariableList = self.globalVariableProvider()
        pickerWidget = GlobalVarPickerWidget(self)
        pickerWidget.setVariableDataList(
            [
                {
                    "key": item.key,
                    "value": item.value,
                    "description": item.description,
                }
                for item in globalVariableList
            ]
        )

        if pickerWidget.exec() != QDialog.DialogCode.Accepted:
            return

        selectedKey = pickerWidget.getSelectedVariableKey()
        if not selectedKey:
            return

        self.insertTextAtCursor(f"${selectedKey}$")
        self.updatePreview()

    def insertTextAtCursor(self, text: str) -> None:
        cursorPosition = self.templateEdit.cursorPosition()
        currentText = self.templateEdit.text()
        updatedText = f"{currentText[:cursorPosition]}{text}{currentText[cursorPosition:]}"
        self.templateEdit.setText(updatedText)
        self.templateEdit.setCursorPosition(cursorPosition + len(text))

    def onSaveClicked(self) -> None:
        variableDataList = self.collectVariableData()
        self.saveRequested.emit(
            self.currentCommandId,
            self.currentCategoryId,
            self.nameEdit.text(),
            self.descriptionEdit.toPlainText(),
            self.templateEdit.text(),
            variableDataList,
        )
