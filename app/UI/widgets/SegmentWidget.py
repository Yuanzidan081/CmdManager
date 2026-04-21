from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
)


class SegmentWidget(QFrame):
    dataChanged = pyqtSignal()

    def __init__(self, variableKey: str, variableValue: str = ""):
        super().__init__()
        self.setObjectName("segmentCard")
        self.variableKey = variableKey

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # self.keyLabelTitle = QLabel("变量")
        self.keyLabel = QLabel(variableKey)
        self.keyLabel.setObjectName("segmentKeyLabel")

        # self.valueLabel = QLabel("值")
        self.valueEdit = QLineEdit()
        self.valueEdit.setPlaceholderText(f"请输入 {variableKey} 的值")

        # layout.addWidget(self.keyLabelTitle)
        layout.addWidget(self.keyLabel)
        # layout.addWidget(self.valueLabel)
        layout.addWidget(self.valueEdit, 1)

        self.valueEdit.setText(variableValue)

        self.valueEdit.textChanged.connect(self.onDataChanged)

    def onDataChanged(self) -> None:
        self.dataChanged.emit()

    def getData(self) -> dict:
        return {
            "key": self.variableKey,
            "value": self.valueEdit.text(),
        }
