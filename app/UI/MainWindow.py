from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (QApplication, QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
                             QMainWindow, QMessageBox, QPushButton, QSizePolicy, QStackedWidget, QTabWidget,
                             QTextEdit, QVBoxLayout, QWidget, QComboBox)

from Domain.AppState import AppState
from Domain.GlobalVariableModel import GlobalVariableModel
from Domain.VariableValue import VariableValue
from Services.CategoryService import CategoryService
from Services.CommandService import CommandService
from Services.GlobalVariableService import GlobalVariableService
from UI.widgets.GlobalVarWidget import GlobalVarWidget
from UI.widgets.OverviewWidget import OverviewWidget


class EntityDialog(QDialog):
    def __init__(self, title: str, fields: list[tuple[str, str, str]], parent=None):
        super().__init__(parent); self.setWindowTitle(title); self.resize(620, 420)
        root = QVBoxLayout(self); form = QFormLayout(); self.controls = {}
        for key, label, value in fields:
            control = QTextEdit() if key in ("template", "variables", "description") else QLineEdit()
            if isinstance(control, QTextEdit): control.setPlainText(value); control.setMinimumHeight(70 if key != "description" else 50)
            else: control.setText(value)
            form.addRow(label, control); self.controls[key] = control
        root.addLayout(form); buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); root.addWidget(buttons)
    def value(self, key):
        control = self.controls[key]; return control.toPlainText() if isinstance(control, QTextEdit) else control.text()


class MainWindow(QMainWindow):
    def __init__(self, appState: AppState, categoryService: CategoryService, commandService: CommandService, globalVariableService: GlobalVariableService):
        super().__init__(); self.appState = appState; self.categoryService = categoryService; self.commandService = commandService; self.globalVariableService = globalVariableService
        self.setWindowTitle("CmdManager"); self.resize(1280, 780); self.buildUi(); self.refreshCategoryTabs()

    def buildUi(self):
        central = QWidget(); self.setCentralWidget(central); root = QVBoxLayout(central); root.setContentsMargins(20,18,20,18); root.setSpacing(12)
        top = QWidget(); top.setObjectName("topBar"); bar = QHBoxLayout(top); self.titleLabel = QLabel("CmdManager"); self.titleLabel.setObjectName("titleLabel"); bar.addWidget(self.titleLabel)
        self.categoryNameEdit = QLineEdit(); self.categoryNameEdit.setPlaceholderText("分类名称"); self.categoryNameEdit.setFixedWidth(220); bar.addWidget(self.categoryNameEdit); bar.addStretch()
        for text, slot, style in (("新增分类", self.onAddCategory, "primaryButton"), ("重命名分类", self.onRenameCategory, "ghostButton"), ("删除分类", self.onRemoveCategory, "warnButton"), ("保存", self.onSave, "primaryButton"), ("设置", self.onSettings, "ghostButton")):
            button = QPushButton(text); button.setObjectName(style); button.clicked.connect(slot); bar.addWidget(button)
        root.addWidget(top); self.noticeLabel = QLabel(""); self.noticeLabel.setObjectName("noticeInfoLabel"); self.noticeLabel.setWordWrap(True); self.noticeLabel.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred); root.addWidget(self.noticeLabel)
        self.stack = QStackedWidget(); root.addWidget(self.stack, 1); self.listPage = QWidget(); pageLayout = QVBoxLayout(self.listPage); pageLayout.setContentsMargins(0,0,0,0)
        self.tabs = QTabWidget(); self.tabs.setObjectName("categoryTabWidget"); pageLayout.addWidget(self.tabs); self.stack.addWidget(self.listPage)
        self.globalVarWidget = GlobalVarWidget(); self.stack.addWidget(self.globalVarWidget); self.stack.setCurrentWidget(self.listPage)
        self.tabs.currentChanged.connect(self.onTabChanged); self.globalVarWidget.backRequested.connect(lambda: self.stack.setCurrentWidget(self.listPage)); self.globalVarWidget.saveRequested.connect(self.onGlobalSave)

    def refreshCategoryTabs(self):
        selected = self.appState.selectedCategoryId; self.tabs.blockSignals(True); self.tabs.clear(); selectedIndex = -1
        for index, category in enumerate(self.categoryService.listCategory()):
            view = OverviewWidget(category.id); self._connectOverview(view); self.refreshOverview(view)
            self.tabs.addTab(view, category.name)
            if category.id == selected: selectedIndex = index
        if selectedIndex >= 0: self.tabs.setCurrentIndex(selectedIndex)
        elif self.tabs.count(): self.tabs.setCurrentIndex(0); self.appState.selectedCategoryId = self.tabs.widget(0).categoryId
        self.tabs.blockSignals(False); self.onTabChanged(self.tabs.currentIndex())

    def refreshOverview(self, view: OverviewWidget):
        workflows = self.commandService.listWorkflows(view.categoryId); unplanned = self.commandService.listInstances(None)
        # 未编排实例按模板所属分类过滤。
        unplanned = [item for item in unplanned if (template := self.commandService.getTemplate(item.templateId)) and template.categoryId == view.categoryId]
        preview = lambda instanceId: self.shortenText(self.commandService.buildInstancePreview(instanceId), 150)
        status = self.instanceStatus
        view.setData(self.commandService.listTemplates(view.categoryId), workflows, unplanned, preview, status)
        view.setWorkflowInstances({item.id: self.commandService.listInstances(item.id) for item in workflows}, preview, status)

    def _connectOverview(self, view):
        view.addTemplateRequested.connect(self.editTemplate); view.editTemplateRequested.connect(self.editTemplate); view.deleteTemplateRequested.connect(self.deleteTemplate); view.createInstanceRequested.connect(self.createInstance)
        view.editInstanceRequested.connect(self.editInstance); view.deleteInstanceRequested.connect(self.deleteInstance); view.syncInstanceRequested.connect(self.syncInstance); view.runInstanceRequested.connect(self.runInstance); view.moveInstanceRequested.connect(self.moveInstance); view.moveInstanceWorkflowRequested.connect(self.moveInstanceWorkflow)
        view.addWorkflowRequested.connect(self.editWorkflow); view.editWorkflowRequested.connect(self.editWorkflow); view.deleteWorkflowRequested.connect(self.deleteWorkflow); view.runWorkflowRequested.connect(self.runWorkflow)

    def onTabChanged(self, index):
        if index < 0: return
        view = self.tabs.widget(index); self.appState.selectedCategoryId = view.categoryId
        category = self.categoryService.getCategoryById(view.categoryId); self.categoryNameEdit.setText(category.name if category else "")

    def activeCategoryId(self): return self.appState.selectedCategoryId
    def activeView(self): return self.tabs.currentWidget()
    def refreshActive(self):
        view = self.activeView()
        if isinstance(view, OverviewWidget): self.refreshOverview(view)

    def onAddCategory(self):
        try: self.categoryService.addCategory(self.categoryNameEdit.text()); self.refreshCategoryTabs(); self.notice("新增分类成功")
        except ValueError as error: self.notice(str(error), True)
    def onRenameCategory(self):
        try: self.categoryService.renameCategory(self.activeCategoryId(), self.categoryNameEdit.text()); self.refreshCategoryTabs(); self.notice("重命名分类成功")
        except ValueError as error: self.notice(str(error), True)
    def onRemoveCategory(self):
        categoryId = self.activeCategoryId()
        if not categoryId: return
        if QMessageBox.question(self, "删除分类", "将同时删除分类内模板、流程和实例，确定继续吗？") != QMessageBox.StandardButton.Yes: return
        try: self.categoryService.removeCategory(categoryId); self.refreshCategoryTabs(); self.notice("已删除分类")
        except ValueError as error: self.notice(str(error), True)

    def editTemplate(self, templateIdOrCategory):
        template = self.commandService.getTemplate(templateIdOrCategory); categoryId = template.categoryId if template else templateIdOrCategory
        values = "\n".join(f"{x.key}={x.value}" for x in (template.defaultVariables if template else []))
        dialog = EntityDialog("编辑模板" if template else "新增模板", [("name","名称",template.name if template else ""),("description","描述",template.description if template else ""),("template","命令模板",template.template if template else ""),("variables","默认变量（每行 key=value）",values)], self)
        if dialog.exec() != QDialog.DialogCode.Accepted: return
        try:
            saved = self.commandService.saveTemplate(template.id if template else "", categoryId, dialog.value("name"), dialog.value("description"), dialog.value("template"), self.parseValues(dialog.value("variables")))
            self.refreshActive(); self.notice(f"模板已保存：{saved.name}")
        except ValueError as error: self.notice(str(error), True)

    def deleteTemplate(self, templateId):
        try: self.commandService.removeTemplate(templateId); self.refreshActive(); self.notice("模板已删除")
        except ValueError as error: self.notice(str(error), True)

    def chooseWorkflow(self, categoryId):
        workflows = self.commandService.listWorkflows(categoryId)
        if not workflows: self.notice("请先创建流程", True); return None
        dialog = QDialog(self); dialog.setWindowTitle("选择流程"); layout = QVBoxLayout(dialog); combo = QComboBox(); [combo.addItem(x.name, x.id) for x in workflows]; layout.addWidget(combo); buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel); buttons.accepted.connect(dialog.accept); buttons.rejected.connect(dialog.reject); layout.addWidget(buttons)
        return combo.currentData() if dialog.exec() == QDialog.DialogCode.Accepted else None

    def createInstance(self, templateId, workflowId):
        template = self.commandService.getTemplate(templateId)
        if template is None: return
        if workflowId == "choose":
            workflowId = self.chooseWorkflow(template.categoryId)
            if workflowId is None:
                return
        try: self.commandService.createInstance(templateId, workflowId); self.refreshActive(); self.notice("已创建命令实例")
        except ValueError as error: self.notice(str(error), True)

    def editInstance(self, instanceId):
        instance = self.commandService.getInstance(instanceId)
        if instance is None: return
        values = {x.key:x.value for x in instance.templateSnapshot.defaultVariables}; values.update({x.key:x.value for x in instance.variableOverrides})
        dialog = EntityDialog("编辑命令实例", [("name","名称",instance.name),("variables","变量覆盖（每行 key=value）","\n".join(f"{k}={v}" for k,v in values.items()))], self)
        if dialog.exec() != QDialog.DialogCode.Accepted: return
        try: self.commandService.updateInstance(instanceId, dialog.value("name"), self.parseValues(dialog.value("variables")), []); self.refreshActive(); self.notice("实例已保存")
        except ValueError as error: self.notice(str(error), True)

    def syncInstance(self, instanceId):
        try: self.commandService.syncTemplate(instanceId); self.refreshActive(); self.notice("模板已同步；如有新增变量，请编辑实例确认")
        except ValueError as error: self.notice(str(error), True)
    def deleteInstance(self, instanceId):
        try: self.commandService.removeInstance(instanceId); self.refreshActive(); self.notice("实例已删除")
        except ValueError as error: self.notice(str(error), True)
    def moveInstance(self, instanceId, target):
        try: self.commandService.moveInstance(instanceId, target); self.refreshActive()
        except ValueError as error: self.notice(str(error), True)
    def moveInstanceWorkflow(self, instanceId, target):
        instance = self.commandService.getInstance(instanceId); template = self.commandService.getTemplate(instance.templateId) if instance else None
        if target == "choose" and template: target = self.chooseWorkflow(template.categoryId)
        if target == "choose": return
        try: self.commandService.moveToWorkflow(instanceId, target); self.refreshActive(); self.notice("已更新实例编排")
        except ValueError as error: self.notice(str(error), True)

    def editWorkflow(self, workflowIdOrCategory):
        workflow = self.commandService.getWorkflow(workflowIdOrCategory); categoryId = workflow.categoryId if workflow else workflowIdOrCategory
        dialog = EntityDialog("编辑流程" if workflow else "新增流程", [("name","名称",workflow.name if workflow else ""),("description","描述",workflow.description if workflow else "")], self)
        if dialog.exec() != QDialog.DialogCode.Accepted: return
        try: self.commandService.saveWorkflow(workflow.id if workflow else "", categoryId, dialog.value("name"), dialog.value("description")); self.refreshActive(); self.notice("流程已保存")
        except ValueError as error: self.notice(str(error), True)
    def deleteWorkflow(self, workflowId):
        try: self.commandService.removeWorkflow(workflowId); self.refreshActive(); self.notice("流程已删除，步骤已移至未编排")
        except ValueError as error: self.notice(str(error), True)
    def runWorkflow(self, workflowId):
        box = QMessageBox(self); box.setWindowTitle("运行流程"); box.setText("选择失败策略"); stop = box.addButton("失败即中止", QMessageBox.ButtonRole.AcceptRole); cont = box.addButton("失败后继续", QMessageBox.ButtonRole.ActionRole); box.addButton(QMessageBox.StandardButton.Cancel); box.exec()
        if box.clickedButton() not in (stop, cont): return
        try: self.commandService.runWorkflow(workflowId, box.clickedButton() == cont); self.notice("已在新终端运行流程")
        except ValueError as error: self.notice(str(error), True)
    def runInstance(self, instanceId):
        try: self.commandService.runInstance(instanceId); self.notice("已在新终端运行命令")
        except ValueError as error: self.notice(str(error), True)

    def onSave(self):
        try: self.commandService.saveAll(); self.notice("保存成功")
        except Exception as error: self.notice(f"保存失败：{error}", True)
    def onSettings(self):
        self.globalVarWidget.setGlobalVariableDataList([{"key":x.key,"value":x.value} for x in self.globalVariableService.listGlobalVariable()]); self.stack.setCurrentWidget(self.globalVarWidget)
    def onGlobalSave(self, rows):
        try:
            self.globalVariableService.replaceAll([GlobalVariableModel.fromDict(x) for x in rows]); self.commandService.saveAll(); self.refreshActive(); self.notice("全局变量保存成功")
        except (ValueError, Exception) as error: self.notice(str(error), True)

    def parseValues(self, text):
        result = []
        for line in text.splitlines():
            if not line.strip(): continue
            if "=" not in line: raise ValueError("变量格式应为 key=value")
            key, value = line.split("=", 1); key = key.strip()
            if not key: raise ValueError("变量名不能为空")
            result.append(VariableValue(key, value.strip()))
        return result
    def instanceStatus(self, instance):
        if instance.pendingVariableKeys: return "待确认：" + ", ".join(instance.pendingVariableKeys)
        template = self.commandService.getTemplate(instance.templateId)
        return "模板有更新" if template and instance.templateRevision < template.revision else "已同步"
    def shortenText(self, text, length): return text if len(text) <= length else text[:length-3] + "..."
    def notice(self, message, error=False):
        self.noticeLabel.setText(message); self.noticeLabel.setObjectName("noticeErrorLabel" if error else "noticeInfoLabel"); self.noticeLabel.style().unpolish(self.noticeLabel); self.noticeLabel.style().polish(self.noticeLabel)
    def closeEvent(self, event: QCloseEvent):
        if self.appState.hasDirty:
            try: self.commandService.saveAll()
            except Exception: pass
        event.accept()