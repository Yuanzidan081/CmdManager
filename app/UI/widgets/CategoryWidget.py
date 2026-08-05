from typing import Callable

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from Domain.CommandModel import CommandModel
from UI.widgets.CommandCardWidget import CommandCardWidget


class CategoryWidget(QWidget):
    addCommandRequested = pyqtSignal(str)
    copyCommandRequested = pyqtSignal(str)
    editCommandRequested = pyqtSignal(str)
    runCommandRequested = pyqtSignal(str)
    removeCommandRequested = pyqtSignal(str)
    moveCommandRequested = pyqtSignal(str, int)

    def __init__(self, categoryId: str):
        super().__init__()
        self.categoryId = categoryId

        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(10)
        self.addCommandButton = QPushButton("新增命令")
        self.addCommandButton.setObjectName("primaryButton")
        mainLayout.addWidget(self.addCommandButton, 0)

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("commandScrollArea")
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scrollArea.setFrameShape(QFrame.Shape.NoFrame)
        self.scrollArea.setFrameShadow(QFrame.Shadow.Plain)
        self.scrollArea.setLineWidth(0)
        self.scrollArea.setMidLineWidth(0)
        self.scrollContent = QWidget()
        self.scrollLayout = QVBoxLayout(self.scrollContent)
        self.scrollLayout.setContentsMargins(0, 0, 0, 0)
        self.scrollLayout.setSpacing(12)
        self.scrollLayout.addStretch(1)
        self.scrollArea.setWidget(self.scrollContent)
        mainLayout.addWidget(self.scrollArea, 1)

        self.emptyLabel = QLabel("当前分类还没有命令")
        self.emptyLabel.setObjectName("emptyTipLabel")
        self.addCommandButton.clicked.connect(lambda: self.addCommandRequested.emit(self.categoryId))
        self.setMinimumWidth(950)

    def setCommandList(
        self,
        commandList: list[CommandModel],
        buildPreview: Callable[[str, list], str],
    ) -> None:
        self.clearCommandCardList()
        if not commandList:
            self.scrollLayout.insertWidget(0, self.emptyLabel)
            return

        commandCount = len(commandList)
        for commandIndex, command in enumerate(commandList):
            commandCard = CommandCardWidget(
                command.id,
                command.name,
                command.description,
                buildPreview(command.template, command.variables),
                commandIndex,
                commandCount,
            )
            commandCard.copyClicked.connect(self.copyCommandRequested.emit)
            commandCard.editClicked.connect(self.editCommandRequested.emit)
            commandCard.runClicked.connect(self.runCommandRequested.emit)
            commandCard.removeClicked.connect(self.removeCommandRequested.emit)
            commandCard.moveClicked.connect(self.moveCommandRequested.emit)
            self.scrollLayout.insertWidget(self.scrollLayout.count() - 1, commandCard)

    def clearCommandCardList(self) -> None:
        while self.scrollLayout.count() > 1:
            item = self.scrollLayout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
