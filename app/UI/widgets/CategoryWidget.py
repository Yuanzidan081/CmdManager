from typing import Callable

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget, QPushButton

from Domain.CommandModel import CommandModel
from UI.widgets.CommandCardWidget import CommandCardWidget


class CategoryWidget(QWidget):
    addCommandRequested = pyqtSignal(str)
    editCommandRequested = pyqtSignal(str)
    runCommandRequested = pyqtSignal(str)
    removeCommandRequested = pyqtSignal(str)

    def __init__(self, categoryId: str, categoryName: str):
        super().__init__()
        self.categoryId = categoryId
        self.categoryName = categoryName

        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(10)

        self.addCommandButton = QPushButton("新增命令")
        self.addCommandButton.setObjectName("primaryButton")
        mainLayout.addWidget(self.addCommandButton, 0)

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("commandScrollArea")

        self.scrollContent = QWidget()
        self.scrollLayout = QVBoxLayout(self.scrollContent)
        self.scrollLayout.setContentsMargins(0, 0, 0, 0)
        self.scrollLayout.setSpacing(12)
        self.scrollLayout.addStretch(1)

        self.scrollArea.setWidget(self.scrollContent)
        mainLayout.addWidget(self.scrollArea, 1)

        self.emptyLabel = QLabel("当前分类还没有命令")
        self.emptyLabel.setObjectName("emptyTipLabel")

        self.addCommandButton.clicked.connect(self.onAddCommandClicked)

    def onAddCommandClicked(self) -> None:
        self.addCommandRequested.emit(self.categoryId)

    def setCommandList(
        self,
        commandList: list[CommandModel],
        buildPreview: Callable[[list], str],
    ) -> None:
        self.clearCommandCardList()

        if not commandList:
            self.scrollLayout.insertWidget(0, self.emptyLabel)
            return

        for command in commandList:
            commandPreview = buildPreview(command.segments)
            commandCard = CommandCardWidget(
                command.id,
                command.name,
                command.description,
                commandPreview,
            )
            commandCard.editClicked.connect(self.editCommandRequested.emit)
            commandCard.runClicked.connect(self.runCommandRequested.emit)
            commandCard.removeClicked.connect(self.removeCommandRequested.emit)
            self.scrollLayout.insertWidget(self.scrollLayout.count() - 1, commandCard)

    def clearCommandCardList(self) -> None:
        while self.scrollLayout.count() > 1:
            item = self.scrollLayout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
