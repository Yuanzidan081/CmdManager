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
    QVBoxLayout,
    QWidget,
)

from Domain.CommandModel import CommandModel
from Domain.SegmentModel import SegmentModel
from UI.widgets.SegmentWidget import SegmentWidget


class CommandEditorWidget(QWidget):
    saveRequested = pyqtSignal(str, str, str, str, list)
    backRequested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.currentCommandId = ""
        self.currentCategoryId = ""
        self.previewBuilder: Optional[Callable[[list], str]] = None

        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)

        self.editorScrollArea = QScrollArea()
        self.editorScrollArea.setObjectName("editorScrollArea")
        self.editorScrollArea.setWidgetResizable(True)
        self.editorScrollArea.setFrameShape(QFrame.Shape.NoFrame)
        mainLayout.addWidget(self.editorScrollArea)

        self.editorContent = QWidget()
        self.editorLayout = QVBoxLayout(self.editorContent)
        self.editorLayout.setContentsMargins(0, 0, 0, 0)
        self.editorLayout.setSpacing(12)
        self.editorScrollArea.setWidget(self.editorContent)

        titleLayout = QHBoxLayout()
        self.backButton = QPushButton("返回")
        self.backButton.setObjectName("ghostButton")
        self.titleLabel = QLabel("命令编辑")
        self.titleLabel.setObjectName("pageTitleLabel")
        titleLayout.addWidget(self.backButton)
        titleLayout.addWidget(self.titleLabel)
        titleLayout.addStretch(1)
        self.editorLayout.addLayout(titleLayout)

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

        baseLayout.addWidget(QLabel("名称"))
        baseLayout.addWidget(self.nameEdit)
        baseLayout.addWidget(QLabel("描述"))
        baseLayout.addWidget(self.descriptionEdit)

        self.editorLayout.addWidget(baseCard)

        segmentCard = QFrame()
        segmentCard.setObjectName("editorCard")
        segmentLayout = QVBoxLayout(segmentCard)
        segmentLayout.setContentsMargins(14, 14, 14, 14)
        segmentLayout.setSpacing(10)

        actionLayout = QHBoxLayout()
        self.addLiteralButton = QPushButton("新增 literal")
        self.addLiteralButton.setObjectName("ghostButton")
        self.addVariableButton = QPushButton("新增 variable")
        self.addVariableButton.setObjectName("ghostButton")
        actionLayout.addWidget(self.addLiteralButton)
        actionLayout.addWidget(self.addVariableButton)
        actionLayout.addStretch(1)
        segmentLayout.addLayout(actionLayout)

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
        previewLayout.addWidget(QLabel("命令预览"))
        self.previewLabel = QLabel("")
        self.previewLabel.setObjectName("commandPreviewLabel")
        self.previewLabel.setWordWrap(True)
        previewLayout.addWidget(self.previewLabel)

        saveLayout = QHBoxLayout()
        saveLayout.addStretch(1)
        self.saveButton = QPushButton("保存")
        self.saveButton.setObjectName("primaryButton")
        saveLayout.addWidget(self.saveButton)
        previewLayout.addLayout(saveLayout)

        self.editorLayout.addWidget(previewCard)
        self.editorLayout.addStretch(1)

        self.backButton.clicked.connect(self.backRequested.emit)
        self.addLiteralButton.clicked.connect(self.onAddLiteralClicked)
        self.addVariableButton.clicked.connect(self.onAddVariableClicked)
        self.nameEdit.textChanged.connect(self.updatePreview)
        self.descriptionEdit.textChanged.connect(self.updatePreview)
        self.saveButton.clicked.connect(self.onSaveClicked)

    def setPreviewBuilder(self, previewBuilder: Callable[[list], str]) -> None:
        self.previewBuilder = previewBuilder

    def setNewCommand(self, categoryId: str) -> None:
        self.currentCommandId = ""
        self.currentCategoryId = categoryId
        self.nameEdit.clear()
        self.descriptionEdit.clear()
        self.clearSegmentList()
        self.addSegment("literal", "")
        self.updatePreview()

    def loadCommand(self, command: CommandModel) -> None:
        self.currentCommandId = command.id
        self.currentCategoryId = command.categoryId
        self.nameEdit.setText(command.name)
        self.descriptionEdit.setText(command.description)
        self.clearSegmentList()

        if not command.segments:
            self.addSegment("literal", "")
        else:
            for segment in command.segments:
                self.addSegment(segment.type, segment.value)
        self.updatePreview()

    def onAddLiteralClicked(self) -> None:
        self.addSegment("literal", "")

    def onAddVariableClicked(self) -> None:
        self.addSegment("variable", "")

    def addSegment(self, segmentType: str, segmentValue: str) -> None:
        segmentWidget = SegmentWidget(segmentType, segmentValue)
        segmentWidget.dataChanged.connect(self.updatePreview)
        segmentWidget.removeRequested.connect(self.removeSegment)
        segmentWidget.moveUpRequested.connect(self.moveSegmentUp)
        segmentWidget.moveDownRequested.connect(self.moveSegmentDown)
        self.segmentListLayout.insertWidget(self.segmentListLayout.count() - 1, segmentWidget)
        self.updatePreview()

    def removeSegment(self, segmentWidget: SegmentWidget) -> None:
        if self.segmentListLayout.count() <= 2:
            return
        segmentWidget.setParent(None)
        segmentWidget.deleteLater()
        self.updatePreview()

    def moveSegmentUp(self, segmentWidget: SegmentWidget) -> None:
        index = self.findSegmentIndex(segmentWidget)
        if index <= 0:
            return
        self.segmentListLayout.removeWidget(segmentWidget)
        self.segmentListLayout.insertWidget(index - 1, segmentWidget)
        self.updatePreview()

    def moveSegmentDown(self, segmentWidget: SegmentWidget) -> None:
        index = self.findSegmentIndex(segmentWidget)
        if index < 0 or index >= self.segmentListLayout.count() - 2:
            return
        self.segmentListLayout.removeWidget(segmentWidget)
        self.segmentListLayout.insertWidget(index + 1, segmentWidget)
        self.updatePreview()

    def findSegmentIndex(self, segmentWidget: SegmentWidget) -> int:
        for index in range(self.segmentListLayout.count() - 1):
            layoutItem = self.segmentListLayout.itemAt(index)
            if layoutItem is not None and layoutItem.widget() is segmentWidget:
                return index
        return -1

    def clearSegmentList(self) -> None:
        while self.segmentListLayout.count() > 1:
            layoutItem = self.segmentListLayout.takeAt(0)
            widget = layoutItem.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

    def collectSegmentData(self) -> list[dict]:
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
        segmentDataList = self.collectSegmentData()
        segmentList = [SegmentModel.fromDict(item) for item in segmentDataList]

        if self.previewBuilder is None:
            preview = " ".join([segment.value for segment in segmentList if segment.value.strip()])
        else:
            preview = self.previewBuilder(segmentList)

        self.previewLabel.setText(preview)

    def onSaveClicked(self) -> None:
        segmentDataList = self.collectSegmentData()
        self.saveRequested.emit(
            self.currentCommandId,
            self.currentCategoryId,
            self.nameEdit.text(),
            self.descriptionEdit.toPlainText(),
            segmentDataList,
        )
