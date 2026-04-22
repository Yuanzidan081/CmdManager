from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)


class ElidedPreviewLabel(QLabel):
    def __init__(self, text: str = ""):
        super().__init__()
        self._fullText = ""
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.setMinimumWidth(0)
        self.setText(text)

    def setText(self, text: str) -> None:
        self._fullText = text or ""
        self.setToolTip(self._fullText)
        self.refreshElidedText()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.refreshElidedText()

    def refreshElidedText(self) -> None:
        availableWidth = max(self.contentsRect().width(), 1)

        elidedText = self.fontMetrics().elidedText(
            self._fullText,
            Qt.TextElideMode.ElideRight,
            availableWidth,
        )
        super().setText(elidedText)


class CommandCardWidget(QFrame):
    copyClicked = pyqtSignal(str)
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

        self.previewLabel = ElidedPreviewLabel(commandPreview)
        self.previewLabel.setObjectName("commandPreviewLabel")
        self.previewLabel.setWordWrap(False)
        self.setToolTip(commandPreview)

        infoLayout.addWidget(self.nameLabel)
        infoLayout.addWidget(self.descriptionLabel)
        infoLayout.addWidget(self.previewLabel)

        actionLayout = QHBoxLayout()
        actionLayout.setSpacing(8)

        self.copyButton = QPushButton("复制")
        self.copyButton.setObjectName("ghostButton")
        self.runButton = QPushButton("运行")
        self.runButton.setObjectName("primaryButton")
        self.editButton = QPushButton("编辑")
        self.editButton.setObjectName("ghostButton")
        self.removeButton = QPushButton("删除")
        self.removeButton.setObjectName("warnButton")

        actionLayout.addWidget(self.copyButton)
        actionLayout.addWidget(self.runButton)
        actionLayout.addWidget(self.editButton)
        actionLayout.addWidget(self.removeButton)

        mainLayout.addLayout(infoLayout, 1)
        mainLayout.addLayout(actionLayout)

        self.copyButton.clicked.connect(self.onCopyClicked)
        self.runButton.clicked.connect(self.onRunClicked)
        self.editButton.clicked.connect(self.onEditClicked)
        self.removeButton.clicked.connect(self.onRemoveClicked)

    def onCopyClicked(self) -> None:
        self.copyClicked.emit(self.commandId)

    def onRunClicked(self) -> None:
        self.runClicked.emit(self.commandId)

    def onEditClicked(self) -> None:
        self.editClicked.emit(self.commandId)

    def onRemoveClicked(self) -> None:
        self.removeClicked.emit(self.commandId)
