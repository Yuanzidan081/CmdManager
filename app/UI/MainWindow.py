from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from Domain.AppState import AppState
from Domain.SegmentModel import SegmentModel
from Services.CategoryService import CategoryService
from Services.CommandService import CommandService
from UI.widgets.CategoryWidget import CategoryWidget
from UI.widgets.CommandEditorWidget import CommandEditorWidget


class MainWindow(QMainWindow):
    def __init__(
        self,
        appState: AppState,
        categoryService: CategoryService,
        commandService: CommandService,
    ):
        super().__init__()
        self.appState = appState
        self.categoryService = categoryService
        self.commandService = commandService

        self.setWindowTitle("CmdManager")
        self.resize(1080, 720)

        self.buildUi()
        self.refreshCategoryTabs()

    def buildUi(self) -> None:
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)

        rootLayout = QVBoxLayout(centralWidget)
        rootLayout.setContentsMargins(20, 18, 20, 18)
        rootLayout.setSpacing(12)

        topBarWidget = QWidget()
        topBarWidget.setObjectName("topBar")
        topBarLayout = QHBoxLayout(topBarWidget)
        topBarLayout.setContentsMargins(12, 10, 12, 10)
        topBarLayout.setSpacing(8)

        self.titleLabel = QLabel("CmdManager")
        self.titleLabel.setObjectName("titleLabel")
        topBarLayout.addWidget(self.titleLabel)

        self.categoryNameEdit = QLineEdit()
        self.categoryNameEdit.setPlaceholderText("输入分类名称（用于新增/重命名）")
        self.categoryNameEdit.setFixedWidth(250)
        topBarLayout.addWidget(self.categoryNameEdit)

        topBarLayout.addStretch(1)

        self.addCategoryButton = QPushButton("新增分类")
        self.addCategoryButton.setObjectName("primaryButton")

        self.renameCategoryButton = QPushButton("重命名分类")
        self.renameCategoryButton.setObjectName("ghostButton")

        self.removeCategoryButton = QPushButton("删除分类")
        self.removeCategoryButton.setObjectName("warnButton")

        self.saveButton = QPushButton("保存")
        self.saveButton.setObjectName("primaryButton")

        self.settingButton = QPushButton("设置")
        self.settingButton.setObjectName("ghostButton")

        topBarLayout.addWidget(self.addCategoryButton)
        topBarLayout.addWidget(self.renameCategoryButton)
        topBarLayout.addWidget(self.removeCategoryButton)
        topBarLayout.addWidget(self.saveButton)
        topBarLayout.addWidget(self.settingButton)

        rootLayout.addWidget(topBarWidget)

        self.noticeLabel = QLabel("")
        self.noticeLabel.setObjectName("noticeInfoLabel")
        self.noticeLabel.setWordWrap(True)
        self.noticeLabel.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        rootLayout.addWidget(self.noticeLabel)

        self.pageStack = QStackedWidget()
        rootLayout.addWidget(self.pageStack, 1)

        self.commandListPage = QWidget()
        commandListLayout = QVBoxLayout(self.commandListPage)
        commandListLayout.setContentsMargins(0, 0, 0, 0)
        commandListLayout.setSpacing(0)

        self.categoryTabWidget = QTabWidget()
        self.categoryTabWidget.setObjectName("categoryTabWidget")
        self.categoryTabWidget.setDocumentMode(True)
        self.categoryTabWidget.tabBar().setDrawBase(False)
        commandListLayout.addWidget(self.categoryTabWidget)

        self.commandEditorWidget = CommandEditorWidget()
        self.commandEditorWidget.setPreviewBuilder(self.commandService.buildCommandPreview)
        self.commandEditorWidget.setTemplateParser(self.commandService.parseTemplateVariables)

        self.pageStack.addWidget(self.commandListPage)
        self.pageStack.addWidget(self.commandEditorWidget)
        self.pageStack.setCurrentWidget(self.commandListPage)

        self.addCategoryButton.clicked.connect(self.onAddCategoryClicked)
        self.renameCategoryButton.clicked.connect(self.onRenameCategoryClicked)
        self.removeCategoryButton.clicked.connect(self.onRemoveCategoryClicked)
        self.saveButton.clicked.connect(self.onSaveClicked)
        self.settingButton.clicked.connect(self.onSettingClicked)
        self.categoryTabWidget.currentChanged.connect(self.onCategoryTabChanged)

        self.commandEditorWidget.saveRequested.connect(self.onEditorSaveRequested)
        self.commandEditorWidget.backRequested.connect(self.onEditorBackRequested)

    def refreshCategoryTabs(self) -> None:
        selectedCategoryId = self.appState.selectedCategoryId

        self.categoryTabWidget.blockSignals(True)
        self.categoryTabWidget.clear()

        categoryList = self.categoryService.listCategory()
        selectedIndex = -1

        for index, category in enumerate(categoryList):
            categoryWidget = CategoryWidget(category.id)
            commandList = self.commandService.listCommand(category.id)
            categoryWidget.setCommandList(commandList, self.commandService.buildCommandPreview)
            categoryWidget.addCommandRequested.connect(self.onAddCommandRequested)
            categoryWidget.copyCommandRequested.connect(self.onCopyCommandRequested)
            categoryWidget.editCommandRequested.connect(self.onEditCommandRequested)
            categoryWidget.runCommandRequested.connect(self.onRunCommandRequested)
            categoryWidget.removeCommandRequested.connect(self.onRemoveCommandRequested)
            self.categoryTabWidget.addTab(categoryWidget, category.name)
            if category.id == selectedCategoryId:
                selectedIndex = index

        if selectedIndex >= 0:
            self.categoryTabWidget.setCurrentIndex(selectedIndex)
        elif categoryList:
            self.categoryTabWidget.setCurrentIndex(0)
            self.appState.selectedCategoryId = categoryList[0].id
        else:
            self.appState.selectedCategoryId = None

        self.categoryTabWidget.blockSignals(False)
        self.onCategoryTabChanged(self.categoryTabWidget.currentIndex())

    def onCategoryTabChanged(self, index: int) -> None:
        if index < 0:
            self.appState.selectedCategoryId = None
            self.categoryNameEdit.clear()
            return
        tabWidget = self.categoryTabWidget.widget(index)
        if isinstance(tabWidget, CategoryWidget):
            self.appState.selectedCategoryId = tabWidget.categoryId
            category = self.categoryService.getCategoryById(tabWidget.categoryId)
            if category is not None:
                self.categoryNameEdit.setText(category.name)

    def onAddCategoryClicked(self) -> None:
        text = self.categoryNameEdit.text().strip()
        if not text:
            self.showNotice("请输入分类名称", True)
            return

        try:
            self.categoryService.addCategory(text)
            self.refreshCategoryTabs()
            self.categoryNameEdit.clear()
            self.showNotice("新增分类成功")
        except ValueError as error:
            self.showNotice(str(error), True)

    def onRenameCategoryClicked(self) -> None:
        categoryId = self.appState.selectedCategoryId
        if not categoryId:
            self.showNotice("请先选择分类", True)
            return

        category = self.categoryService.getCategoryById(categoryId)
        if category is None:
            self.showNotice("分类不存在", True)
            return

        text = self.categoryNameEdit.text().strip()
        if not text:
            self.showNotice("请输入新分类名称", True)
            return

        try:
            self.categoryService.renameCategory(categoryId, text)
            self.refreshCategoryTabs()
            self.showNotice("重命名分类成功")
        except ValueError as error:
            self.showNotice(str(error), True)

    def onRemoveCategoryClicked(self) -> None:
        categoryId = self.appState.selectedCategoryId
        if not categoryId:
            self.showNotice("请先选择分类", True)
            return

        commandCount = self.commandService.countCommandInCategory(categoryId)
        try:
            self.categoryService.removeCategory(categoryId)
            self.refreshCategoryTabs()
            self.showNotice(f"已删除分类，关联命令 {commandCount} 条")
        except ValueError as error:
            self.showNotice(str(error), True)

    def onAddCommandRequested(self, categoryId: str) -> None:
        self.commandEditorWidget.setNewCommand(categoryId)
        self.pageStack.setCurrentWidget(self.commandEditorWidget)

    def onEditCommandRequested(self, commandId: str) -> None:
        command = self.commandService.getCommandById(commandId)
        if command is None:
            self.showNotice("命令不存在", True)
            return

        self.commandEditorWidget.loadCommand(command)
        self.pageStack.setCurrentWidget(self.commandEditorWidget)

    def onCopyCommandRequested(self, commandId: str) -> None:
        try:
            copiedCommand = self.commandService.copyCommand(commandId)
            self.refreshCategoryTabs()
            self.showNotice(f"已复制命令：{copiedCommand.name}")
            self.onEditCommandRequested(copiedCommand.id)
        except ValueError as error:
            self.showNotice(str(error), True)

    def onRunCommandRequested(self, commandId: str) -> None:
        try:
            commandText = self.commandService.runCommand(commandId)
            shortCommandText = self.shortenText(commandText, 120)
            self.showNotice(
                f"已在新窗口执行命令：{shortCommandText}",
                False,
                commandText,
            )
        except ValueError as error:
            self.showNotice(str(error), True)

    def onRemoveCommandRequested(self, commandId: str) -> None:
        command = self.commandService.getCommandById(commandId)
        if command is None:
            self.showNotice("命令不存在", True)
            return
        self.commandService.removeCommand(commandId)
        self.refreshCategoryTabs()
        self.showNotice(f"已删除命令：{command.name}")

    def onEditorSaveRequested(
        self,
        commandId: str,
        categoryId: str,
        name: str,
        description: str,
        template: str,
        variableDataList: list,
    ) -> None:
        variableList = [SegmentModel.fromDict(item) for item in variableDataList]
        try:
            if commandId:
                self.commandService.updateCommand(
                    commandId,
                    name,
                    description,
                    template,
                    variableList,
                )
            else:
                self.commandService.addCommand(
                    categoryId,
                    name,
                    description,
                    template,
                    variableList,
                )
            self.refreshCategoryTabs()
            self.pageStack.setCurrentWidget(self.commandListPage)
            self.showNotice("命令保存成功")
        except ValueError as error:
            self.showNotice(str(error), True)

    def onEditorBackRequested(self) -> None:
        self.pageStack.setCurrentWidget(self.commandListPage)

    def onSaveClicked(self) -> None:
        try:
            self.commandService.saveAll()
            self.showNotice("保存成功")
        except Exception as error:
            self.showNotice(f"保存失败：{error}", True)

    def onSettingClicked(self) -> None:
        self.showNotice("设置功能将在下一阶段实现")

    def shortenText(self, text: str, maxLength: int) -> str:
        if maxLength <= 0:
            return ""
        if len(text) <= maxLength:
            return text
        if maxLength <= 3:
            return "." * maxLength
        return f"{text[:maxLength - 3]}..."

    def showNotice(self, message: str, isError: bool = False, tooltipText: str = "") -> None:
        self.noticeLabel.setText(message)
        self.noticeLabel.setToolTip(tooltipText if tooltipText else message)
        if isError:
            self.noticeLabel.setObjectName("noticeErrorLabel")
        else:
            self.noticeLabel.setObjectName("noticeInfoLabel")
        self.noticeLabel.style().unpolish(self.noticeLabel)
        self.noticeLabel.style().polish(self.noticeLabel)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.appState.hasDirty:
            try:
                self.commandService.saveAll()
            except Exception:
                pass
        event.accept()
