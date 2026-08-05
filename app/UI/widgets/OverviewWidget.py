from typing import Callable

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QScrollArea, QSplitter, QVBoxLayout, QWidget)

from Domain.CommandInstance import CommandInstance
from Domain.CommandTemplate import CommandTemplate
from Domain.Workflow import Workflow


class OverviewWidget(QWidget):
    addTemplateRequested = pyqtSignal(str)
    editTemplateRequested = pyqtSignal(str)
    deleteTemplateRequested = pyqtSignal(str)
    createInstanceRequested = pyqtSignal(str, object)
    editInstanceRequested = pyqtSignal(str)
    deleteInstanceRequested = pyqtSignal(str)
    syncInstanceRequested = pyqtSignal(str)
    runInstanceRequested = pyqtSignal(str)
    moveInstanceRequested = pyqtSignal(str, int)
    moveInstanceWorkflowRequested = pyqtSignal(str, object)
    addWorkflowRequested = pyqtSignal(str)
    editWorkflowRequested = pyqtSignal(str)
    deleteWorkflowRequested = pyqtSignal(str)
    runWorkflowRequested = pyqtSignal(str)

    def __init__(self, categoryId: str):
        super().__init__(); self.categoryId = categoryId; self._templates = []
        root = QHBoxLayout(self); root.setContentsMargins(0, 10, 0, 0)
        self.splitter = QSplitter(Qt.Orientation.Horizontal); root.addWidget(self.splitter)
        self.templatePanel = QWidget(); left = QVBoxLayout(self.templatePanel); left.setContentsMargins(0, 0, 8, 0)
        bar = QHBoxLayout(); self.searchEdit = QLineEdit(); self.searchEdit.setPlaceholderText("搜索模板")
        self.addTemplateButton = QPushButton("新增模板"); self.addTemplateButton.setObjectName("primaryButton")
        self.collapseButton = QPushButton("‹"); self.collapseButton.setFixedWidth(36)
        bar.addWidget(self.searchEdit, 1); bar.addWidget(self.addTemplateButton); bar.addWidget(self.collapseButton); left.addLayout(bar)
        self.templateLayout = self._scrollLayout(); left.addWidget(self.templateScroll, 1)
        self.workflowPanel = QWidget(); right = QVBoxLayout(self.workflowPanel); right.setContentsMargins(8, 0, 0, 0)
        title = QHBoxLayout(); label = QLabel("流程"); label.setObjectName("pageTitleLabel"); self.addWorkflowButton = QPushButton("新增流程"); self.addWorkflowButton.setObjectName("primaryButton")
        title.addWidget(label); title.addStretch(); title.addWidget(self.addWorkflowButton); right.addLayout(title)
        self.workflowLayout = self._scrollLayout(); right.addWidget(self.workflowScroll, 1)
        self.splitter.addWidget(self.templatePanel); self.splitter.addWidget(self.workflowPanel); self.splitter.setSizes([390, 690])
        self.searchEdit.textChanged.connect(lambda: self.renderTemplates(self._templates))
        self.addTemplateButton.clicked.connect(lambda: self.addTemplateRequested.emit(self.categoryId))
        self.addWorkflowButton.clicked.connect(lambda: self.addWorkflowRequested.emit(self.categoryId))
        self.collapseButton.clicked.connect(self.toggleTemplates)

    def _scrollLayout(self):
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget(); layout = QVBoxLayout(content); layout.setContentsMargins(0, 8, 0, 0); layout.setSpacing(8); layout.addStretch()
        scroll.setWidget(content)
        if not hasattr(self, 'templateScroll'): self.templateScroll = scroll
        else: self.workflowScroll = scroll
        return layout

    def toggleTemplates(self):
        hidden = self.templatePanel.isHidden(); self.templatePanel.setVisible(hidden); self.collapseButton.setText("‹" if hidden else "›")

    def setData(self, templates, workflows, unplanned, preview: Callable[[str], str], status: Callable[[CommandInstance], str]):
        self._templates = templates; self.renderTemplates(templates); self._clear(self.workflowLayout)
        self.workflowLayout.insertWidget(0, self._section("未编排命令", unplanned, preview, status, None))
        for workflow in workflows: self.workflowLayout.insertWidget(self.workflowLayout.count()-1, self._workflowCard(workflow, [x for x in unplanned if False], preview, status))
        # workflow instances are attached by MainWindow after the widget is created.

    def setWorkflowInstances(self, mapping, preview, status):
        # Rebuild right side while retaining the already supplied workflow ordering.
        for index in range(self.workflowLayout.count()-1):
            widget = self.workflowLayout.itemAt(index).widget()
            if widget and hasattr(widget, 'workflowId'):
                layout = widget.findChild(QWidget, 'stepsContainer').layout()
                self._clear(layout)
                steps = mapping.get(widget.workflowId, [])
                for pos, item in enumerate(steps): layout.insertWidget(layout.count()-1, self._instanceCard(item, preview, status, pos, len(steps), widget.workflowId))

    def renderTemplates(self, templates):
        self._clear(self.templateLayout); key = self.searchEdit.text().strip().lower()
        for item in templates:
            if key and key not in (item.name + item.description + item.template).lower(): continue
            card = QFrame(); card.setObjectName("commandCard"); box = QVBoxLayout(card); box.setContentsMargins(12, 10, 12, 10)
            name = QLabel(item.name); name.setObjectName("commandNameLabel"); preview = QLabel(item.template); preview.setObjectName("commandCardPreviewLabel"); preview.setWordWrap(True)
            actions = QHBoxLayout(); add = QPushButton("添加到流程"); loose = QPushButton("未编排"); edit = QPushButton("编辑"); remove = QPushButton("删除"); remove.setObjectName("warnButton")
            for button in (add, loose, edit, remove): actions.addWidget(button)
            box.addWidget(name); box.addWidget(preview); box.addLayout(actions)
            add.clicked.connect(lambda _, x=item.id: self.createInstanceRequested.emit(x, "choose")); loose.clicked.connect(lambda _, x=item.id: self.createInstanceRequested.emit(x, None))
            edit.clicked.connect(lambda _, x=item.id: self.editTemplateRequested.emit(x)); remove.clicked.connect(lambda _, x=item.id: self.deleteTemplateRequested.emit(x))
            self.templateLayout.insertWidget(self.templateLayout.count()-1, card)

    def _section(self, title, instances, preview, status, workflowId):
        card = QFrame(); card.setObjectName("editorCard"); box = QVBoxLayout(card); box.setContentsMargins(12, 10, 12, 10)
        label = QLabel(title); label.setObjectName("pageTitleLabel"); box.addWidget(label)
        for pos, item in enumerate(instances): box.addWidget(self._instanceCard(item, preview, status, pos, len(instances), workflowId))
        return card

    def _workflowCard(self, workflow, _instances, preview, status):
        card = QFrame(); card.workflowId = workflow.id; card.setObjectName("editorCard")
        box = QVBoxLayout(card); box.setContentsMargins(12, 10, 12, 10)
        header = QHBoxLayout(); name = QLabel(workflow.name); name.setObjectName("pageTitleLabel"); run = QPushButton("运行流程"); run.setObjectName("primaryButton"); edit = QPushButton("编辑"); remove = QPushButton("删除"); remove.setObjectName("warnButton")
        header.addWidget(name); header.addStretch(); [header.addWidget(x) for x in (run, edit, remove)]; box.addLayout(header)
        container = QWidget(); container.setObjectName("stepsContainer"); steps = QVBoxLayout(container); steps.setContentsMargins(0, 4, 0, 0); steps.setSpacing(6); steps.addStretch(); box.addWidget(container)
        run.clicked.connect(lambda _, x=workflow.id: self.runWorkflowRequested.emit(x)); edit.clicked.connect(lambda _, x=workflow.id: self.editWorkflowRequested.emit(x)); remove.clicked.connect(lambda _, x=workflow.id: self.deleteWorkflowRequested.emit(x))
        return card

    def _instanceCard(self, item, preview, status, pos, total, workflowId):
        card = QFrame(); card.setObjectName("commandCard"); box = QHBoxLayout(card); box.setContentsMargins(10, 8, 10, 8)
        info = QVBoxLayout(); name = QLabel(item.name); name.setObjectName("commandNameLabel"); line = QLabel(preview(item.id)); line.setObjectName("commandCardPreviewLabel"); line.setToolTip(preview(item.id)); state = QLabel(status(item)); state.setObjectName("noticeErrorLabel" if "待确认" in status(item) else "noticeInfoLabel")
        info.addWidget(name); info.addWidget(line); info.addWidget(state); box.addLayout(info); box.addStretch()
        run = QPushButton("运行"); sync = QPushButton("同步"); up = QPushButton("上移"); down = QPushButton("下移"); edit = QPushButton("编辑"); move = QPushButton("移出流程" if workflowId else "加入流程"); remove = QPushButton("删除"); remove.setObjectName("warnButton")
        up.setEnabled(pos > 0); down.setEnabled(pos < total-1)
        for b in (run,sync,up,down,edit,move,remove): box.addWidget(b)
        run.clicked.connect(lambda _, x=item.id: self.runInstanceRequested.emit(x)); sync.clicked.connect(lambda _, x=item.id: self.syncInstanceRequested.emit(x)); up.clicked.connect(lambda _, x=item.id, p=pos-1: self.moveInstanceRequested.emit(x,p)); down.clicked.connect(lambda _, x=item.id, p=pos+1: self.moveInstanceRequested.emit(x,p)); edit.clicked.connect(lambda _, x=item.id: self.editInstanceRequested.emit(x)); move.clicked.connect(lambda _, x=item.id, target=workflowId: self.moveInstanceWorkflowRequested.emit(x, None if target else "choose")); remove.clicked.connect(lambda _, x=item.id: self.deleteInstanceRequested.emit(x))
        return card

    @staticmethod
    def _clear(layout):
        while layout.count() > 1:
            item = layout.takeAt(0); widget = item.widget()
            if widget: widget.deleteLater()