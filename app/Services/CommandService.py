import re
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from Base.JsonBase import JsonBase
from Base.TerminalBase import TerminalBase
from Domain.AppState import AppState
from Domain.CategoryModel import CategoryModel
from Domain.CommandInstance import CommandInstance, TemplateSnapshot
from Domain.CommandModel import CommandModel
from Domain.CommandTemplate import CommandTemplate
from Domain.GlobalVariableModel import GlobalVariableModel
from Domain.VariableValue import VariableValue
from Domain.Workflow import Workflow


TemplateVariablePattern = re.compile(r"%([^%\s]+)%")
GlobalVariablePattern = re.compile(r"\$([A-Za-z0-9_]+)\$")


class CommandService:
    """数据仓储和命令构建的统一入口。"""
    def __init__(self, appState: AppState, jsonBase: JsonBase, terminalBase: TerminalBase, dataFilePath: str):
        self.appState = appState
        self.jsonBase = jsonBase
        self.terminalBase = terminalBase
        self.dataFilePath = dataFilePath

    def loadAll(self) -> None:
        data = self.jsonBase.loadFromFile(self.dataFilePath)
        if int(data.get("schemaVersion", 0)) < 2 and data.get("commands"):
            data = self.migrateLegacyData(data)
        self.appState.categoryList = self._loadCategories(data.get("categories", []))
        self.appState.templateList = [CommandTemplate.fromDict(item) for item in data.get("templates", [])]
        self.appState.instanceList = [CommandInstance.fromDict(item) for item in data.get("instances", [])]
        self.appState.workflowList = [Workflow.fromDict(item) for item in data.get("workflows", [])]
        self.appState.globalVariableList = [GlobalVariableModel.fromDict(item) for item in data.get("globalVariables", []) if str(item.get("key", "")).strip()]
        self.normalizeAllOrders()
        validIds = {item.id for item in self.appState.categoryList}
        if self.appState.selectedCategoryId not in validIds:
            self.appState.selectedCategoryId = self.appState.categoryList[0].id if self.appState.categoryList else None
        self.appState.hasDirty = False

    def saveAll(self) -> None:
        self.normalizeAllOrders()
        data = {
            "schemaVersion": 2,
            "categories": [item.toDict() for item in self.appState.categoryList],
            "templates": [item.toDict() for item in self.appState.templateList],
            "instances": [item.toDict() for item in self.appState.instanceList],
            "workflows": [item.toDict() for item in self.appState.workflowList],
            "globalVariables": [item.toDict() for item in self.appState.globalVariableList],
        }
        self.jsonBase.saveToFile(self.dataFilePath, data)
        self.appState.hasDirty = False

    def migrateLegacyData(self, data: dict) -> dict:
        source = Path(self.dataFilePath)
        if source.exists():
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup = source.with_name(f"{source.stem}.backup-{stamp}{source.suffix}")
            try:
                shutil.copy2(source, backup)
            except OSError as error:
                raise RuntimeError(f"旧数据备份失败：{error}") from error
        grouped: dict[str, CommandTemplate] = {}
        instances: list[CommandInstance] = []
        for raw in data.get("commands", []):
            legacy = CommandModel.fromDict(raw)
            if not legacy.template:
                continue
            template = grouped.get(legacy.template)
            legacyValues = {item.key: item.value for item in legacy.variables}
            if template is None:
                defaults = [VariableValue(item.key, item.value) for item in legacy.variables]
                template = CommandTemplate(str(uuid.uuid4()), legacy.categoryId, legacy.name, legacy.description, legacy.template, defaults, 1)
                grouped[legacy.template] = template
            defaults = {item.key: item.value for item in template.defaultVariables}
            overrides = [VariableValue(key, value) for key, value in legacyValues.items() if defaults.get(key, "") != value]
            instances.append(CommandInstance(str(uuid.uuid4()), template.id, None, legacy.name, len(instances),
                TemplateSnapshot(template.template, [VariableValue(x.key, x.value) for x in template.defaultVariables]),
                1, overrides, []))
        migrated = {
            "schemaVersion": 2, "categories": data.get("categories", []),
            "templates": [item.toDict() for item in grouped.values()],
            "instances": [item.toDict() for item in instances], "workflows": [],
            "globalVariables": data.get("globalVariables", []),
        }
        self.jsonBase.saveToFile(self.dataFilePath, migrated)
        return migrated

    def _loadCategories(self, source: list[dict]) -> list[CategoryModel]:
        result = sorted([CategoryModel.fromDict(item) for item in source], key=lambda item: item.order)
        for index, item in enumerate(result): item.order = index
        return result

    def parseTemplateVariables(self, template: str) -> list[str]:
        seen, result = set(), []
        for match in TemplateVariablePattern.finditer(template):
            key = match.group(1).strip()
            if key and key not in seen:
                seen.add(key); result.append(key)
        return result

    def normalizeVariables(self, template: str, values: list[VariableValue]) -> list[VariableValue]:
        valueMap = {item.key.strip(): item.value for item in values if item.key.strip()}
        return [VariableValue(key, valueMap.get(key, "")) for key in self.parseTemplateVariables(template)]

    def getTemplate(self, templateId: str) -> Optional[CommandTemplate]:
        return next((item for item in self.appState.templateList if item.id == templateId), None)

    def getInstance(self, instanceId: str) -> Optional[CommandInstance]:
        return next((item for item in self.appState.instanceList if item.id == instanceId), None)

    def getWorkflow(self, workflowId: str) -> Optional[Workflow]:
        return next((item for item in self.appState.workflowList if item.id == workflowId), None)

    def listTemplates(self, categoryId: str, keyword: str = "") -> list[CommandTemplate]:
        needle = keyword.strip().lower()
        result = [item for item in self.appState.templateList if item.categoryId == categoryId]
        if needle: result = [item for item in result if needle in item.name.lower() or needle in item.description.lower() or needle in item.template.lower()]
        return sorted(result, key=lambda item: item.name.lower())

    def saveTemplate(self, templateId: str, categoryId: str, name: str, description: str, templateText: str, values: list[VariableValue]) -> CommandTemplate:
        name, templateText = name.strip(), templateText.strip()
        if not name: raise ValueError("模板名称不能为空")
        if not templateText: raise ValueError("命令模板不能为空")
        defaults = self.normalizeVariables(templateText, values)
        if templateId:
            item = self.getTemplate(templateId)
            if item is None: raise ValueError("模板不存在")
            item.name, item.description, item.template, item.defaultVariables = name, description.strip(), templateText, defaults
            item.revision += 1
        else:
            item = CommandTemplate(str(uuid.uuid4()), categoryId, name, description.strip(), templateText, defaults, 1)
            self.appState.templateList.append(item)
        self.appState.hasDirty = True
        return item

    def removeTemplate(self, templateId: str) -> None:
        count = sum(item.templateId == templateId for item in self.appState.instanceList)
        if count: raise ValueError(f"模板仍被 {count} 个实例引用，无法删除")
        self.appState.templateList = [item for item in self.appState.templateList if item.id != templateId]
        self.appState.hasDirty = True

    def createInstance(self, templateId: str, workflowId: Optional[str] = None) -> CommandInstance:
        template = self.getTemplate(templateId)
        if template is None: raise ValueError("模板不存在")
        if workflowId and self.getWorkflow(workflowId) is None: raise ValueError("流程不存在")
        instance = CommandInstance(str(uuid.uuid4()), templateId, workflowId, template.name,
            self._nextInstanceOrder(workflowId), TemplateSnapshot(template.template, [VariableValue(x.key, x.value) for x in template.defaultVariables]),
            template.revision, [], [])
        self.appState.instanceList.append(instance); self.normalizeInstanceOrder(workflowId); self.appState.hasDirty = True
        return instance

    def updateInstance(self, instanceId: str, name: str, overrides: list[VariableValue], pending: Optional[list[str]] = None) -> CommandInstance:
        item = self.getInstance(instanceId)
        if item is None: raise ValueError("实例不存在")
        name = name.strip()
        if not name: raise ValueError("实例名称不能为空")
        allowed = self.parseTemplateVariables(item.templateSnapshot.template)
        mapping = {value.key.strip(): value.value for value in overrides if value.key.strip() in allowed}
        defaults = {value.key: value.value for value in item.templateSnapshot.defaultVariables}
        item.name = name
        item.variableOverrides = [VariableValue(key, mapping[key]) for key in allowed if key in mapping and mapping[key] != defaults.get(key, "")]
        item.pendingVariableKeys = [key for key in (pending or []) if key in allowed and key not in mapping]
        self.appState.hasDirty = True
        return item

    def syncTemplate(self, instanceId: str) -> CommandInstance:
        item = self.getInstance(instanceId)
        if item is None: raise ValueError("实例不存在")
        template = self.getTemplate(item.templateId)
        if template is None: raise ValueError("关联模板不存在")
        oldKeys = set(self.parseTemplateVariables(item.templateSnapshot.template))
        oldOverrides = {value.key: value.value for value in item.variableOverrides}
        newKeys = self.parseTemplateVariables(template.template)
        item.templateSnapshot = TemplateSnapshot(template.template, [VariableValue(x.key, x.value) for x in template.defaultVariables])
        item.variableOverrides = [VariableValue(key, oldOverrides[key]) for key in newKeys if key in oldOverrides]
        item.pendingVariableKeys = [key for key in newKeys if key not in oldKeys]
        item.templateRevision = template.revision
        self.appState.hasDirty = True
        return item

    def listInstances(self, workflowId: Optional[str]) -> list[CommandInstance]:
        return sorted([item for item in self.appState.instanceList if item.workflowId == workflowId], key=lambda item: (item.order, item.id))

    def moveInstance(self, instanceId: str, targetIndex: int) -> None:
        item = self.getInstance(instanceId)
        if item is None: raise ValueError("实例不存在")
        group = self.listInstances(item.workflowId)
        source = next(index for index, value in enumerate(group) if value.id == instanceId)
        if targetIndex < 0 or targetIndex >= len(group): raise ValueError("实例排序目标无效")
        group.insert(targetIndex, group.pop(source))
        for index, value in enumerate(group): value.order = index
        self.appState.hasDirty = True

    def moveToWorkflow(self, instanceId: str, workflowId: Optional[str]) -> None:
        item = self.getInstance(instanceId)
        if item is None: raise ValueError("实例不存在")
        if workflowId and self.getWorkflow(workflowId) is None: raise ValueError("流程不存在")
        old = item.workflowId; item.workflowId = workflowId; item.order = self._nextInstanceOrder(workflowId)
        self.normalizeInstanceOrder(old); self.normalizeInstanceOrder(workflowId); self.appState.hasDirty = True

    def removeInstance(self, instanceId: str) -> None:
        item = self.getInstance(instanceId)
        if item is None: raise ValueError("实例不存在")
        group = item.workflowId; self.appState.instanceList = [x for x in self.appState.instanceList if x.id != instanceId]
        self.normalizeInstanceOrder(group); self.appState.hasDirty = True

    def listWorkflows(self, categoryId: str) -> list[Workflow]:
        return sorted([item for item in self.appState.workflowList if item.categoryId == categoryId], key=lambda item: (item.order, item.id))

    def saveWorkflow(self, workflowId: str, categoryId: str, name: str, description: str) -> Workflow:
        name = name.strip()
        if not name: raise ValueError("流程名称不能为空")
        if workflowId:
            item = self.getWorkflow(workflowId)
            if item is None: raise ValueError("流程不存在")
            item.name, item.description = name, description.strip()
        else:
            item = Workflow(str(uuid.uuid4()), categoryId, name, description.strip(), len(self.listWorkflows(categoryId)))
            self.appState.workflowList.append(item)
        self.appState.hasDirty = True; return item

    def removeWorkflow(self, workflowId: str) -> None:
        workflow = self.getWorkflow(workflowId)
        if workflow is None: raise ValueError("流程不存在")
        for instance in self.appState.instanceList:
            if instance.workflowId == workflowId: instance.workflowId = None
        self.appState.workflowList = [item for item in self.appState.workflowList if item.id != workflowId]
        self.normalizeInstanceOrder(None); self.normalizeWorkflowOrder(workflow.categoryId); self.appState.hasDirty = True

    def buildCommandPreview(self, template: str, variables: list, globalVariables: Optional[list[GlobalVariableModel]] = None) -> str:
        if not template.strip(): return ""
        values = [VariableValue(getattr(x, "key", ""), getattr(x, "value", "")) for x in variables]
        return self.buildFinalCommand(TemplateSnapshot(template, values), [], globalVariables)

    def buildInstancePreview(self, instanceId: str) -> str:
        item = self.getInstance(instanceId)
        if item is None: raise ValueError("实例不存在")
        return self.buildFinalCommand(item.templateSnapshot, item.variableOverrides)

    def buildFinalCommand(self, snapshot: TemplateSnapshot, overrides: list[VariableValue], globalVariables: Optional[list[GlobalVariableModel]] = None) -> str:
        text = snapshot.template.strip()
        globals_ = globalVariables if globalVariables is not None else self.appState.globalVariableList
        globalMap = {item.key.strip(): item.value for item in globals_ if item.key.strip()}
        text = GlobalVariablePattern.sub(lambda match: self.quoteIfNeed(globalMap[match.group(1)]) if match.group(1) in globalMap else match.group(0), text)
        values = {item.key: item.value for item in snapshot.defaultVariables}; values.update({item.key: item.value for item in overrides})
        for key in self.parseTemplateVariables(text): text = text.replace(f"%{key}%", self.quoteIfNeed(values.get(key, "")))
        return text

    def runInstance(self, instanceId: str) -> str:
        instance = self.getInstance(instanceId)
        if instance is None: raise ValueError("实例不存在")
        if instance.pendingVariableKeys: raise ValueError("实例存在待确认变量：" + ", ".join(instance.pendingVariableKeys))
        text = self.buildInstancePreview(instanceId)
        self._validateExecutable(text); self.terminalBase.run(text); return text

    def runWorkflow(self, workflowId: str, continueOnFailure: bool = False) -> str:
        workflow = self.getWorkflow(workflowId)
        if workflow is None: raise ValueError("流程不存在")
        commands = []
        for index, instance in enumerate(self.listInstances(workflowId), 1):
            if instance.pendingVariableKeys: raise ValueError(f"步骤 {instance.name} 存在待确认变量")
            text = self.buildInstancePreview(instance.id); self._validateExecutable(text)
            prefix = f'echo === [{index}] {instance.name} === & '
            commands.append(prefix + text)
        if not commands: raise ValueError("流程没有步骤")
        joiner = " & " if continueOnFailure else " && "
        text = joiner.join(commands); self.terminalBase.run(text); return text

    def _validateExecutable(self, text: str) -> None:
        unresolved = self.parseTemplateVariables(text) + self.parseGlobalVariableKeys(text)
        if unresolved: raise ValueError("存在未解析变量：" + ", ".join(unresolved))
        if not text.strip(): raise ValueError("命令内容为空")

    def parseGlobalVariableKeys(self, text: str) -> list[str]:
        return list(dict.fromkeys(match.group(1).strip() for match in GlobalVariablePattern.finditer(text) if match.group(1).strip()))

    def quoteIfNeed(self, value: str) -> str:
        value = str(value).strip()
        if not value: return ""
        if len(value) >= 2 and value[0] == '"' and value[-1] == '"': value = value[1:-1].strip()
        if " " not in value and "\t" not in value: return value
        return '"' + value.replace('"', '""') + '"'

    def _nextInstanceOrder(self, workflowId: Optional[str]) -> int: return len(self.listInstances(workflowId))
    def normalizeInstanceOrder(self, workflowId: Optional[str]) -> None:
        for index, item in enumerate(self.listInstances(workflowId)): item.order = index
    def normalizeWorkflowOrder(self, categoryId: str) -> None:
        for index, item in enumerate(self.listWorkflows(categoryId)): item.order = index
    def normalizeAllOrders(self) -> None:
        for category in self.appState.categoryList:
            self.normalizeWorkflowOrder(category.id)
        for workflow in self.appState.workflowList: self.normalizeInstanceOrder(workflow.id)
        self.normalizeInstanceOrder(None)