# CmdManager 详细设计

## 1. 目标与范围

本设计落实 [架构说明](./cli-generator-architecture.md) 的“模板 → 实例 → 流程”模型，将当前扁平的命令卡片列表调整为可复用、可编排的命令管理界面。

本期包含：模板、实例、流程、按实例同步模板、流程执行、旧数据迁移，以及已有分类、全局变量、预览复制和单步运行能力的兼容。流程不支持跳过步骤，也不提供模板修改后的批量强制同步。

## 2. 数据模型与持久化

### 2.1 模型

```python
@dataclass
class VariableValue:
    key: str
    value: str = ""

@dataclass
class TemplateSnapshot:
    template: str
    defaultVariables: list[VariableValue]

@dataclass
class CommandTemplate:
    id: str
    categoryId: str
    name: str
    description: str
    template: str
    defaultVariables: list[VariableValue]
    revision: int = 1

@dataclass
class CommandInstance:
    id: str
    templateId: str
    workflowId: str | None
    name: str
    order: int
    templateSnapshot: TemplateSnapshot
    templateRevision: int
    variableOverrides: list[VariableValue]
    pendingVariableKeys: list[str]

@dataclass
class Workflow:
    id: str
    categoryId: str
    name: str
    description: str
    order: int
```

`Category` 和 `GlobalVariableModel` 延续现有字段。所有 `id` 全局唯一；模板、流程必须引用存在的分类；实例必须引用存在的模板；实例的 `workflowId` 为空表示未编排。

### 2.2 JSON 结构

`data/commands.json` 保存为单一文档：

```json
{
  "schemaVersion": 2,
  "categories": [{ "id": "simpleperf", "name": "SimplePerf", "order": 0 }],
  "templates": [{
    "id": "tpl-record",
    "categoryId": "simpleperf",
    "name": "record",
    "description": "采集性能数据",
    "template": "adb shell simpleperf record -o %output% -app %package%",
    "defaultVariables": [{ "key": "output", "value": "/data/local/tmp/perf.data" }],
    "revision": 3
  }],
  "instances": [{
    "id": "ins-record-3new",
    "templateId": "tpl-record",
    "workflowId": "wf-3new",
    "name": "record-3new",
    "order": 0,
    "templateSnapshot": {
      "template": "adb shell simpleperf record -o %output% -app %package%",
      "defaultVariables": [{ "key": "output", "value": "/data/local/tmp/perf.data" }]
    },
    "templateRevision": 3,
    "variableOverrides": [{ "key": "package", "value": "com.example.app" }],
    "pendingVariableKeys": []
  }],
  "workflows": [{ "id": "wf-3new", "categoryId": "simpleperf", "name": "3new", "description": "", "order": 0 }],
  "globalVariables": [{ "key": "SDK_ROOT", "value": "E:\\sdk", "description": "" }]
}
```

保存前校验并归一化排序：同一分类的流程、同一流程的实例，`order` 均连续为 `0..n-1`。模板本身不需要排序字段，按名称显示；需要手动排序时再新增 `order` 字段及迁移规则。

### 2.3 变量和值的有效来源

实例有效变量由 `templateSnapshot.defaultVariables` 和 `variableOverrides` 合并得到：同名覆盖值优先。`pendingVariableKeys` 只记录需要确认的键，不参与值合并。

模板变量以命令文本中 `%key%` 的首次出现顺序为准；保存模板时自动去重，并删除 `defaultVariables` 中不再存在的键。实例同步时按该顺序重建快照变量。

## 3. 服务层设计

### 3.1 TemplateService

```python
listTemplates(categoryId: str, keyword: str = "") -> list[CommandTemplate]
createTemplate(payload: TemplatePayload) -> CommandTemplate
updateTemplate(templateId: str, payload: TemplatePayload) -> CommandTemplate
deleteTemplate(templateId: str) -> None
parseVariableKeys(template: str) -> list[str]
```

- 新建模板的 `revision` 为 `1`；每次成功更新递增一次。
- 删除前查询实例引用。存在引用时禁止删除，并提示引用数量，避免产生孤儿实例。
- `updateTemplate` 只修改模板，不触碰实例快照、覆盖值或待处理状态。

### 3.2 InstanceService

```python
createInstance(templateId: str, workflowId: str | None, name: str | None = None) -> CommandInstance
listInstances(workflowId: str | None) -> list[CommandInstance]
updateInstance(instanceId: str, name: str, overrides: list[VariableValue], pendingKeys: list[str]) -> CommandInstance
syncTemplate(instanceId: str) -> CommandInstance
moveInstance(instanceId: str, targetIndex: int) -> None
moveToWorkflow(instanceId: str, workflowId: str | None, targetIndex: int | None = None) -> None
buildCommandPreview(instanceId: str) -> str
runInstance(instanceId: str) -> None
```

创建实例时复制模板文本、默认变量和当前 `revision` 到快照；默认名称采用模板名称，可在编辑时修改。实例编辑只允许改名称和覆盖值，不能直接修改快照命令文本。

`syncTemplate` 的步骤：

1. 读取关联模板及旧实例覆盖值。
2. 使用模板当前命令文本和默认变量重建 `templateSnapshot`。
3. 保留键名仍存在的覆盖值；删除已不存在的覆盖值。
4. 对新增键、或模板变量重命名后无法继承原覆盖值的键，写入 `pendingVariableKeys`；值取模板默认值，默认值不存在时为空字符串。
5. 更新 `templateRevision` 为模板 `revision`，标记数据已修改。

实例卡片同步状态按 `templateRevision < template.revision` 判断；存在 `pendingVariableKeys` 时优先显示“待确认”。

### 3.3 WorkflowService

```python
listWorkflows(categoryId: str) -> list[Workflow]
createWorkflow(categoryId: str, name: str, description: str) -> Workflow
updateWorkflow(workflowId: str, name: str, description: str) -> Workflow
deleteWorkflow(workflowId: str) -> None
moveWorkflow(workflowId: str, targetIndex: int) -> None
runWorkflow(workflowId: str, failurePolicy: FailurePolicy) -> None
```

删除流程不删除其中实例，而是将它们的 `workflowId` 设为空，并重新编号未编排实例。流程排序仅影响同一分类。

### 3.4 命令构建和运行

所有预览、复制、单步运行和流程运行均调用同一个构建函数：

```python
buildFinalCommand(snapshot: TemplateSnapshot,
                  overrides: list[VariableValue],
                  globalVariables: list[GlobalVariableModel]) -> str
```

处理顺序固定为：合并快照默认值与覆盖值 → 替换 `$全局变量$` → 替换 `%命令变量%` → Windows 参数引号和转义。未解析的变量保留原文本；执行前统一校验，存在未解析变量或待确认变量时阻止运行并指出键名。复制预览允许复制当前文本，但需提示其包含未解析变量。

## 4. 界面与交互

### 4.1 主界面

`MainWindow` 保留分类 Tab 和全局变量入口。分类内容采用 `QSplitter` 双栏布局：

- 左栏“模板库”：搜索框、新建模板按钮、可折叠的模板卡片列表；折叠箭头收起/恢复整栏。
- 右栏“流程”：新建流程按钮、未编排命令区和流程卡片列表。
- 模板卡片提供编辑、删除、“添加到流程”和“创建未编排实例”。“添加到流程”使用流程选择弹窗，确认后创建新实例，不复用已存在实例。

主窗口负责页面切换、调用服务、剪贴板写入、错误提示及变更后刷新；Widget 不直接读写 JSON 或拼接命令。

### 4.2 流程与实例卡片

流程卡片头部显示名称、描述、展开/收起、运行流程、编辑、删除，以及流程上移/下移。展开后按 `order` 显示实例卡片。

实例卡片显示名称、单行命令预览、所属模板名和同步状态，操作顺序为：复制、运行、同步模板、上移、下移、编辑、移出流程。未编排区的实例不显示“移出流程”，而提供“加入流程”。首项禁用上移，末项禁用下移。

同步状态：

| 条件 | 显示 |
| --- | --- |
| `pendingVariableKeys` 非空 | 红色“待确认” |
| 实例版本低于模板版本 | 黄色“模板有更新” |
| 其他 | 灰色“已同步” |

### 4.3 统一编辑页

编辑页根据对象类型显示不同表单：

| 对象 | 可编辑内容 | 只读内容 |
| --- | --- | --- |
| 模板 | 名称、描述、命令文本、默认变量 | 当前版本号 |
| 实例 | 名称、变量覆盖值、待确认字段 | 模板名、快照命令文本、同步版本 |
| 流程 | 名称、描述 | 流程步骤 |

模板编辑时解析变量文本，生成默认值输入项。实例编辑时显示有效值；覆盖值与模板默认值相同则在保存时删除该覆盖项。待确认字段采用红色边框和提示文字；用户填写或确认该字段后，将其从 `pendingVariableKeys` 移除。

命令预览区右侧保留“复制”按钮。预览变化时刷新按钮状态；空预览禁用复制。点击后只向 `MainWindow` 发出文本，由主窗口写入系统剪贴板并提示结果。

### 4.4 流程运行

点击“运行流程”后先显示模式选择对话框：

- `STOP_ON_FAILURE`：失败即中止，默认选项。
- `CONTINUE_ON_FAILURE`：记录失败并继续后续步骤。

确认后先校验所有步骤；任一步不可执行则不启动终端并显示步骤名称和原因。通过校验后，在同一新 cmd 窗口中按排序执行；每步输出 `=== [序号/总数] 实例名 ===`。中止模式以 `&&` 连接；继续模式以独立命令和错误码输出连接。单步运行沿用现有终端启动方式。

## 5. 事件时序

### 5.1 添加模板到流程

1. 用户在模板卡片点击“添加到流程”并选择目标流程。
2. `MainWindow` 调用 `InstanceService.createInstance(templateId, workflowId)`。
3. 服务生成当前模板快照，追加到目标流程末尾并重新编号。
4. 主窗口刷新模板库和流程区。

### 5.2 单实例同步

1. 用户在有更新或待确认状态的实例卡片点击“同步模板”。
2. 主窗口调用 `InstanceService.syncTemplate(instanceId)`。
3. 服务按同步规则更新快照、覆盖值、待确认键和版本。
4. 主窗口打开或刷新实例编辑页；待确认键以红色提示。

### 5.3 排序或移动

1. 用户点击实例上移、下移或加入/移出流程。
2. 服务只调整受影响容器的实例列表，并写回连续 `order`。
3. 所有写操作设定 `AppState.hasDirty = True`；保存成功后清除。

## 6. 旧数据迁移

加载时按 `schemaVersion` 决定是否迁移。缺少版本号或存在旧 `commands` 数组即视为旧格式：

1. 在同目录创建 `commands.backup-YYYYMMDD-HHmmss.json`，备份失败则停止迁移并提示。
2. 保留分类和全局变量；按旧命令 `template` 的完全一致文本分组，每组创建一个模板。
3. 每条旧命令创建一个未编排实例：命令文本和原变量作为快照；与组选定默认值不同的变量进入覆盖值。
4. 不创建任何流程，也不推断 SimplePerf 的业务组。
5. 写入 `schemaVersion: 2` 后再进入正常加载流程。

迁移必须可重复执行：只有旧格式会触发迁移，已是版本 2 的文件不再创建备份或重复生成数据。

## 7. 校验、异常与验收

- 名称去除首尾空白，模板、流程名称不能为空；同分类内模板和流程名称分别唯一。
- 命令模板不能为空；变量键不能为空且唯一。
- 删除模板有实例引用时拒绝；删除流程将实例归入未编排区。
- JSON 读取或保存失败时显示原因；保存失败保留脏状态。
- 剪贴板失败仅提示，不改变数据状态。

验收应覆盖：模板修改不影响未同步实例；同步保留匹配覆盖值并标红新增待确认变量；实例可加入、移出、排序并持久化；流程按两种失败策略在同一终端执行；旧数据先备份后去重迁移，且不自动生成业务流程；已有预览复制、分类和全局变量功能仍可用。