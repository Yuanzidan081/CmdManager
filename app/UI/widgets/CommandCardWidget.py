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
        self.maxDisplayWidth = max(1, maxDisplayWidth)
        # self.setMinimumWidth(0)
        # self.setMaximumWidth(self.maxDisplayWidth)
        # self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.setFixedWidth(self.maxDisplayWidth)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.setText(text)

    def setMaxDisplayWidth(self, maxDisplayWidth: int) -> None:
        self.maxDisplayWidth = max(1, maxDisplayWidth)
        self.setMaximumWidth(self.maxDisplayWidth)
        self.refreshElidedText()

    def setText(self, text: str) -> None:
        self.fullText = text or ""
        self.setToolTip(self.fullText)
        self.refreshElidedText()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.refreshElidedText()

    def refreshElidedText(self) -> None:
        visibleWidth = max(self.contentsRect().width(), 1)
        fullTextWidth = self.fontMetrics().horizontalAdvance(self.fullText)
        # if fullTextWidth <= visibleWidth:
        #     super().setText(self.fullText)
        #     return

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

        self.previewLabel = FixedElidedPreviewLabel(
            commandPreview,
            maxDisplayWidth=self.previewMaxDisplayWidth,
        )
        self.previewLabel.setObjectName("commandCardPreviewLabel")
        self.previewLabel.setWordWrap(False)

        infoLayout.addWidget(self.nameLabel)
        infoLayout.addWidget(self.previewLabel)

        tooltipText = (commandPreview or "").strip()
        if not tooltipText:
            tooltipText = (commandDescription or "").strip()
        if not tooltipText:
            tooltipText = commandName
        self.setToolTip(tooltipText)
        self.nameLabel.setToolTip(tooltipText)
        self.previewLabel.setToolTip(tooltipText)

        actionLayout = QHBoxLayout()
        actionLayout.setSpacing(8)

        self.copyButton = QPushButton("复制")
        self.copyButton.setObjectName("ghostButton")
        self.copyButton.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.runButton = QPushButton("运行")
        self.runButton.setObjectName("primaryButton")
        self.runButton.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.editButton = QPushButton("编辑")
        self.editButton.setObjectName("ghostButton")
        self.editButton.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.removeButton = QPushButton("删除")
        self.removeButton.setObjectName("warnButton")
        self.removeButton.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        actionLayout.addWidget(self.copyButton)
        actionLayout.addWidget(self.runButton)
        actionLayout.addWidget(self.editButton)
        actionLayout.addWidget(self.removeButton)

        mainLayout.addLayout(infoLayout, 0)
        mainLayout.addStretch(1)
        mainLayout.addLayout(actionLayout, 0)

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
