from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)


class GlobalVarPickerWidget(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("插入全局变量")
        self.resize(520, 420)
        self.variableDataList: list[dict] = []

        rootLayout = QVBoxLayout(self)
        rootLayout.setContentsMargins(12, 12, 12, 12)
        rootLayout.setSpacing(10)

        titleLabel = QLabel("选择全局变量（支持搜索）")
        titleLabel.setObjectName("pageTitleLabel")
        rootLayout.addWidget(titleLabel)

        self.searchEdit = QLineEdit()
        self.searchEdit.setPlaceholderText("输入变量名或值进行搜索")
        rootLayout.addWidget(self.searchEdit)

        self.variableListWidget = QListWidget()
        self.variableListWidget.setObjectName("editorScrollArea")
        rootLayout.addWidget(self.variableListWidget, 1)

        actionLayout = QHBoxLayout()
        actionLayout.addStretch(1)
        self.cancelButton = QPushButton("取消")
        self.cancelButton.setObjectName("ghostButton")
        self.addButton = QPushButton("添加")
        self.addButton.setObjectName("primaryButton")
        actionLayout.addWidget(self.cancelButton)
        actionLayout.addWidget(self.addButton)
        rootLayout.addLayout(actionLayout)

        self.searchEdit.textChanged.connect(self.applyFilter)
        self.variableListWidget.itemDoubleClicked.connect(self.onItemDoubleClicked)
        self.cancelButton.clicked.connect(self.reject)
        self.addButton.clicked.connect(self.onAddClicked)

    def setVariableDataList(self, variableDataList: list[dict]) -> None:
        self.variableDataList = list(variableDataList)
        self.applyFilter()

    def applyFilter(self) -> None:
        keyword = self.searchEdit.text().strip().lower()
        self.variableListWidget.clear()

        for item in self.variableDataList:
            key = str(item.get("key", "")).strip()
            value = str(item.get("value", ""))
            if not key:
                continue

            searchableText = f"{key} {value}".lower()
            if keyword and keyword not in searchableText:
                continue

            displayText = f"{key}    {value}"
            listItem = QListWidgetItem(displayText)
            listItem.setData(Qt.ItemDataRole.UserRole, key)

            listItem.setToolTip(f"{key} = {value}")

            self.variableListWidget.addItem(listItem)

        if self.variableListWidget.count() > 0:
            self.variableListWidget.setCurrentRow(0)

    def getSelectedVariableKey(self) -> str:
        item = self.variableListWidget.currentItem()
        if item is None:
            return ""
        return str(item.data(Qt.ItemDataRole.UserRole) or "").strip()

    def onItemDoubleClicked(self, _item: QListWidgetItem) -> None:
        self.accept()

    def onAddClicked(self) -> None:
        if not self.getSelectedVariableKey():
            return
        self.accept()
