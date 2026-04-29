from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class GlobalVarWidget(QWidget):
    backRequested = pyqtSignal()
    saveRequested = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.isSortAscending = True

        rootLayout = QVBoxLayout(self)
        rootLayout.setContentsMargins(0, 0, 0, 0)
        rootLayout.setSpacing(10)

        headerLayout = QHBoxLayout()
        self.backButton = QPushButton("返回")
        self.backButton.setObjectName("ghostButton")
        self.titleLabel = QLabel("设置 / 全局变量")
        self.titleLabel.setObjectName("pageTitleLabel")
        headerLayout.addWidget(self.backButton)
        headerLayout.addWidget(self.titleLabel)
        headerLayout.addStretch(1)
        rootLayout.addLayout(headerLayout)

        toolCard = QFrame()
        toolCard.setObjectName("editorCard")
        toolLayout = QHBoxLayout(toolCard)
        toolLayout.setContentsMargins(12, 10, 12, 10)
        toolLayout.setSpacing(8)

        self.searchEdit = QLineEdit()
        self.searchEdit.setPlaceholderText("搜索全局变量（key/value）")
        self.sortButton = QPushButton("按名称升序")
        self.sortButton.setObjectName("ghostButton")
        self.addButton = QPushButton("新增")
        self.addButton.setObjectName("primaryButton")
        self.removeButton = QPushButton("删除")
        self.removeButton.setObjectName("warnButton")

        toolLayout.addWidget(self.searchEdit, 1)
        toolLayout.addWidget(self.sortButton)
        toolLayout.addWidget(self.addButton)
        toolLayout.addWidget(self.removeButton)
        rootLayout.addWidget(toolCard)

        self.tableWidget = QTableWidget(0, 2)
        self.tableWidget.setHorizontalHeaderLabels(["Key", "Value"])
        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableWidget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.setObjectName("editorScrollArea")
        rootLayout.addWidget(self.tableWidget, 1)

        bottomBar = QWidget()
        bottomBar.setObjectName("editorBottomBar")
        bottomLayout = QHBoxLayout(bottomBar)
        bottomLayout.setContentsMargins(0, 4, 0, 0)
        bottomLayout.addStretch(1)
        self.saveButton = QPushButton("保存")
        self.saveButton.setObjectName("primaryButton")
        bottomLayout.addWidget(self.saveButton)
        rootLayout.addWidget(bottomBar)

        self.backButton.clicked.connect(self.backRequested.emit)
        self.saveButton.clicked.connect(self.onSaveClicked)
        self.addButton.clicked.connect(self.onAddClicked)
        self.removeButton.clicked.connect(self.onRemoveClicked)
        self.sortButton.clicked.connect(self.onSortClicked)
        self.searchEdit.textChanged.connect(self.applyFilter)

    def setGlobalVariableDataList(self, dataList: list[dict]) -> None:
        self.tableWidget.setRowCount(0)
        for data in dataList:
            self.addRow(
                str(data.get("key", "")),
                str(data.get("value", "")),
            )
        self.applyFilter()

    def addRow(self, key: str = "", value: str = "") -> None:
        row = self.tableWidget.rowCount()
        self.tableWidget.insertRow(row)

        keyItem = QTableWidgetItem(key)
        valueItem = QTableWidgetItem(value)

        self.tableWidget.setItem(row, 0, keyItem)
        self.tableWidget.setItem(row, 1, valueItem)

        tooltipText = f"{key} = {value}"
        keyItem.setToolTip(tooltipText)
        valueItem.setToolTip(tooltipText)

    def onAddClicked(self) -> None:
        self.addRow()

    def onRemoveClicked(self) -> None:
        selectedRowList = [index.row() for index in self.tableWidget.selectionModel().selectedRows()]
        for row in sorted(set(selectedRowList), reverse=True):
            self.tableWidget.removeRow(row)

    def onSortClicked(self) -> None:
        sortOrder = Qt.SortOrder.AscendingOrder
        if not self.isSortAscending:
            sortOrder = Qt.SortOrder.DescendingOrder
        self.tableWidget.sortItems(0, sortOrder)
        if self.isSortAscending:
            self.sortButton.setText("按名称降序")
        else:
            self.sortButton.setText("按名称升序")
        self.isSortAscending = not self.isSortAscending

    def applyFilter(self) -> None:
        keyword = self.searchEdit.text().strip().lower()
        rowCount = self.tableWidget.rowCount()
        for row in range(rowCount):
            keyText = self.getCellText(row, 0).lower()
            valueText = self.getCellText(row, 1).lower()
            searchText = f"{keyText} {valueText}"
            isMatched = (not keyword) or (keyword in searchText)
            self.tableWidget.setRowHidden(row, not isMatched)

    def getCellText(self, row: int, column: int) -> str:
        item = self.tableWidget.item(row, column)
        if item is None:
            return ""
        return item.text().strip()

    def collectData(self) -> list[dict]:
        dataList: list[dict] = []
        rowCount = self.tableWidget.rowCount()
        for row in range(rowCount):
            dataList.append(
                {
                    "key": self.getCellText(row, 0),
                    "value": self.getCellText(row, 1),
                }
            )
        return dataList

    def onSaveClicked(self) -> None:
        self.saveRequested.emit(self.collectData())
