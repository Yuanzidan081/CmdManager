from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
)


class SegmentWidget(QFrame):
    dataChanged = pyqtSignal()
    removeRequested = pyqtSignal(object)
    moveUpRequested = pyqtSignal(object)
    moveDownRequested = pyqtSignal(object)

    def __init__(self, segmentType: str = "literal", segmentValue: str = ""):
        super().__init__()
        self.setObjectName("segmentCard")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        self.typeLabel = QLabel("类型")
        self.typeCombo = QComboBox()
        self.typeCombo.addItems(["literal", "variable"])

        self.valueLabel = QLabel("值")
        self.valueEdit = QLineEdit()
        self.valueEdit.setPlaceholderText("请输入片段值")

        self.upButton = QPushButton("上移")
        self.downButton = QPushButton("下移")
        self.removeButton = QPushButton("删除")
        self.removeButton.setObjectName("warnButton")

        layout.addWidget(self.typeLabel)
        layout.addWidget(self.typeCombo)
        layout.addWidget(self.valueLabel)
        layout.addWidget(self.valueEdit, 1)
        layout.addWidget(self.upButton)
        layout.addWidget(self.downButton)
        layout.addWidget(self.removeButton)

        if segmentType in {"literal", "variable"}:
            self.typeCombo.setCurrentText(segmentType)
        self.valueEdit.setText(segmentValue)

        self.typeCombo.currentTextChanged.connect(self.onDataChanged)
        self.valueEdit.textChanged.connect(self.onDataChanged)
        self.removeButton.clicked.connect(self.onRemoveClicked)
        self.upButton.clicked.connect(self.onMoveUpClicked)
        self.downButton.clicked.connect(self.onMoveDownClicked)

    def onDataChanged(self) -> None:
        self.dataChanged.emit()

    def onRemoveClicked(self) -> None:
        self.removeRequested.emit(self)

    def onMoveUpClicked(self) -> None:
        self.moveUpRequested.emit(self)

    def onMoveDownClicked(self) -> None:
        self.moveDownRequested.emit(self)

    def getData(self) -> dict:
        return {
            "type": self.typeCombo.currentText(),
            "value": self.valueEdit.text(),
        }
