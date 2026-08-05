from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)


class FixedElidedPreviewLabel(QLabel):
    def __init__(self, text: str = "", maxDisplayWidth: int = 620):
        super().__init__()
        self.fullText = ""
        self.setFixedWidth(max(1, maxDisplayWidth))
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.setText(text)

    def setText(self, text: str) -> None:
        self.fullText = text or ""
        self.setToolTip(self.fullText)
        self.refreshElidedText()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.refreshElidedText()

    def refreshElidedText(self) -> None:
        visibleWidth = max(self.contentsRect().width(), 1)
        elidedText = self.fontMetrics().elidedText(
            self.fullText,
            Qt.TextElideMode.ElideRight,
            visibleWidth,
        )
        super().setText(elidedText)


class CommandCardWidget(QFrame):
    previewMaxDisplayWidth = 620

    copyClicked = pyqtSignal(str)
    runClicked = pyqtSignal(str)
    moveClicked = pyqtSignal(str, int)
    editClicked = pyqtSignal(str)
    removeClicked = pyqtSignal(str)

    def __init__(
        self,
        commandId: str,
        commandName: str,
        commandDescription: str,
        commandPreview: str,
        commandIndex: int,
        commandCount: int,
    ):
        super().__init__()
        self.commandId = commandId
        self.commandIndex = commandIndex
        self.setObjectName("commandCard")

        mainLayout = QHBoxLayout(self)
        mainLayout.setContentsMargins(16, 14, 16, 14)
        mainLayout.setSpacing(12)

        infoLayout = QVBoxLayout()
        infoLayout.setSpacing(4)
        self.nameLabel = QLabel(commandName)
        self.nameLabel.setObjectName("commandNameLabel")
        self.previewLabel = FixedElidedPreviewLabel(
            commandPreview,
            maxDisplayWidth=self.previewMaxDisplayWidth,
        )
        self.previewLabel.setObjectName("commandCardPreviewLabel")
        self.previewLabel.setWordWrap(False)
        infoLayout.addWidget(self.nameLabel)
        infoLayout.addWidget(self.previewLabel)

        tooltipText = (commandPreview or commandDescription or commandName).strip()
        self.setToolTip(tooltipText)
        self.nameLabel.setToolTip(tooltipText)
        self.previewLabel.setToolTip(tooltipText)

        actionLayout = QHBoxLayout()
        actionLayout.setSpacing(8)
        self.copyButton = self.createButton("复制", "ghostButton")
        self.runButton = self.createButton("运行", "primaryButton")
        self.moveUpButton = self.createButton("上移", "ghostButton")
        self.moveDownButton = self.createButton("下移", "ghostButton")
        self.editButton = self.createButton("编辑", "ghostButton")
        self.removeButton = self.createButton("删除", "warnButton")
        self.moveUpButton.setEnabled(commandIndex > 0)
        self.moveDownButton.setEnabled(commandIndex < commandCount - 1)
        for button in (
            self.copyButton,
            self.runButton,
            self.moveUpButton,
            self.moveDownButton,
            self.editButton,
            self.removeButton,
        ):
            actionLayout.addWidget(button)

        mainLayout.addLayout(infoLayout, 0)
        mainLayout.addStretch(1)
        mainLayout.addLayout(actionLayout, 0)

        self.copyButton.clicked.connect(lambda: self.copyClicked.emit(self.commandId))
        self.runButton.clicked.connect(lambda: self.runClicked.emit(self.commandId))
        self.moveUpButton.clicked.connect(lambda: self.moveClicked.emit(self.commandId, commandIndex - 1))
        self.moveDownButton.clicked.connect(lambda: self.moveClicked.emit(self.commandId, commandIndex + 1))
        self.editButton.clicked.connect(lambda: self.editClicked.emit(self.commandId))
        self.removeButton.clicked.connect(lambda: self.removeClicked.emit(self.commandId))

    def createButton(self, text: str, objectName: str) -> QPushButton:
        button = QPushButton(text)
        button.setObjectName(objectName)
        button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        return button
