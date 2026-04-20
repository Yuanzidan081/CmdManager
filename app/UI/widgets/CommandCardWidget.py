from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout


class CommandCardWidget(QFrame):
    runClicked = pyqtSignal(str)
    editClicked = pyqtSignal(str)
    removeClicked = pyqtSignal(str)

    def __init__(
        self,
        commandId: str,
        commandName: str,
        commandDescription: str,
        commandPreview: str,
    ):
        super().__init__()
        self.commandId = commandId
        self.setObjectName("commandCard")

        mainLayout = QHBoxLayout(self)
        mainLayout.setContentsMargins(16, 14, 16, 14)
        mainLayout.setSpacing(12)

        infoLayout = QVBoxLayout()
        infoLayout.setSpacing(4)

        self.nameLabel = QLabel(commandName)
        self.nameLabel.setObjectName("commandNameLabel")

        self.descriptionLabel = QLabel(commandDescription or "")
        self.descriptionLabel.setObjectName("commandDescriptionLabel")

        self.previewLabel = QLabel(commandPreview)
        self.previewLabel.setObjectName("commandPreviewLabel")

        infoLayout.addWidget(self.nameLabel)
        infoLayout.addWidget(self.descriptionLabel)
        infoLayout.addWidget(self.previewLabel)

        actionLayout = QHBoxLayout()
        actionLayout.setSpacing(8)

        self.runButton = QPushButton("运行")
        self.runButton.setObjectName("primaryButton")
        self.editButton = QPushButton("编辑")
        self.editButton.setObjectName("ghostButton")
        self.removeButton = QPushButton("删除")
        self.removeButton.setObjectName("warnButton")

        actionLayout.addWidget(self.runButton)
        actionLayout.addWidget(self.editButton)
        actionLayout.addWidget(self.removeButton)

        mainLayout.addLayout(infoLayout, 1)
        mainLayout.addLayout(actionLayout)

        self.runButton.clicked.connect(self.onRunClicked)
        self.editButton.clicked.connect(self.onEditClicked)
        self.removeButton.clicked.connect(self.onRemoveClicked)

    def onRunClicked(self) -> None:
        self.runClicked.emit(self.commandId)

    def onEditClicked(self) -> None:
        self.editClicked.emit(self.commandId)

    def onRemoveClicked(self) -> None:
        self.removeClicked.emit(self.commandId)
