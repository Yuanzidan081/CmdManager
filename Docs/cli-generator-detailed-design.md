# CmdManager 详细设计

## 1. 目标与边界

本设计落实 [架构说明](./cli-generator-architecture.md) 中的交互与职责划分。CmdManager 管理分类、命令模板和全局变量，负责生成最终命令、复制到剪贴板或在 Windows 终端运行。

本次增量包含两项：

1. 在命令编辑页的“命令预览”右侧提供复制按钮。
2. 在命令卡片中提供上移、下移操作，仅调整当前分类内的命令顺序。

`CommandService` 是生成最终命令与调整命令顺序的唯一业务入口；UI 不直接拼接命令、不直接写入 `order` 或 JSON。

## 2. 页面与控件

### 2.1 MainWindow

使用 `QStackedWidget` 承载以下页面：

- `CommandListPage`：按当前分类展示命令卡片。
- `CommandEditorPage`：新增或编辑命令。
- `SettingsPage`：管理全局变量。

职责：维护 `AppState`、绑定页面事件、调用 Service、刷新页面，以及统一处理剪贴板和通知。

关键回调：

```python
def onCopyCommandRequested(command: str) -> None
def onMoveCommandRequested(commandId: str, targetIndex: int) -> None
def refreshCommandList() -> None
```

`onCopyCommandRequested` 使用 `QApplication.clipboard().setText(command)` 写入系统剪贴板；成功显示“已复制命令”，失败显示“复制失败：{原因}”。

### 2.2 CategoryWidget

职责：显示分类 Tab 与当前分类的命令卡片列表。

- 新增、重命名、删除分类；删除分类须二次确认，并级联删除其命令。
- 命令列表仅纵向滚动，不显示横向滚动条。
- 本期不支持分类拖拽排序；命令排序由卡片的上移、下移按钮完成。
- 刷新命令列表时，先按 `order` 升序获取当前分类命令，再为每张卡片计算当前位置和总数。

```python
def createCommandCard(command: CommandModel, index: int, total: int) -> CommandCardWidget
def onCardMoveRequested(commandId: str, direction: int) -> None
```

`direction` 为 `-1`（上移）或 `1`（下移）。目标索引越界时不调用 Service。

### 2.3 CommandCardWidget

职责：展示一条已保存命令及其操作。

字段：

1. `name`。
2. `commandPreview`：由 `CommandService.buildCommandPreview` 生成，位于名称下方。

展示规则：

- 预览使用透明、无边框的 `QLabel`，单行省略；最大显示宽度为 620。
- 卡片 tooltip 显示完整最终命令。
- 操作区固定在右侧，窗口拉伸时按钮不拉伸。

操作按钮顺序：复制、运行、上移、下移、编辑、删除。

```python
def setOrderState(index: int, total: int) -> None

copyRequested = pyqtSignal(str)
runRequested = pyqtSignal(str)
moveRequested = pyqtSignal(str, int)
editRequested = pyqtSignal(str)
removeRequested = pyqtSignal(str)
```

`setOrderState` 规则：首项禁用上移；末项禁用下移；仅一项时两个按钮均禁用。上移和下移只改变当前分类的相邻两项。

### 2.4 CommandEditorWidget

布局：

1. 顶部固定区：返回按钮与标题。
2. 中部单一滚动区：名称、描述、模板、变量输入和命令预览。
3. 底部固定区：保存按钮。

命令预览卡片采用标题行布局：左侧“命令预览”，右侧“复制”按钮；下一行显示可换行的预览文本。

```python
def refreshPreview() -> None
def onCopyPreviewClick() -> None

copyPreviewRequested = pyqtSignal(str)
saveRequested = pyqtSignal(dict)
backRequested = pyqtSignal()
```

交互规则：

- 模板变更或变量值变更时调用 `refreshPreview`。
- `refreshPreview` 必须调用注入的 `CommandService.buildCommandPreview`，不能在 Widget 中自行替换变量。
- 预览为空时禁用复制按钮；非空时启用。
- 点击复制仅发出 `copyPreviewRequested(previewText)`，不保存、不执行、不改动模板或变量。
- 模板不能为空；`%变量名%` 自动解析并去重，生成对应 `SegmentWidget`。
- “插入全局变量”从选择器插入 `$变量名$` 到模板输入框当前光标位置。

### 2.5 SegmentWidget 与全局变量页面

`SegmentWidget` 使用“变量名 Label + 值 LineEdit”，输入项随模板变量自动增减。

`SettingsWidget` / `GlobalVarWidget` 提供全局变量的新增、编辑、删除、搜索和名称排序；`key` 非空且全局唯一。`GlobalVarPickerWidget` 支持搜索、滚动、tooltip、双击或回车插入 `$变量名$`。

## 3. 领域模型与 JSON

```python
@dataclass
class SegmentModel:
    key: str
    value: str

@dataclass
class GlobalVariableModel:
    key: str
    value: str
    description: str = ""

@dataclass
class CommandModel:
    id: str
    categoryId: str
    name: str
    description: str
    template: str
    variables: list[SegmentModel] = field(default_factory=list)
    order: int = 0

@dataclass
class CategoryModel:
    id: str
    name: str
    order: int = 0
```

数据存储为 `data/commands.json`：

```json
{
  "categories": [{ "id": "android", "name": "Android", "order": 0 }],
  "commands": [{
    "id": "simpleperf-record",
    "categoryId": "android",
    "name": "simpleperf-record-3new",
    "description": "",
    "template": "adb shell ... %packageName%",
    "variables": [{ "key": "packageName", "value": "com.example.app" }],
    "order": 0
  }],
  "globalVariables": [{ "key": "SDK_ROOT", "value": "E:\\sdk", "description": "" }]
}
```

约束：

- `id` 全局唯一，`categoryId` 必须存在。
- 同一分类内的命令按 `order` 排序；排序后 `order` 必须从 0 开始连续。
- 删除分类时同步删除关联命令。
- 旧 JSON 缺少 `globalVariables` 或 `order` 时，分别按空数组和列表当前位置兼容处理；下次保存写回完整字段。

## 4. 服务层

### 4.1 CommandService

```python
def listCommand(categoryId: str) -> list[CommandModel]
def buildCommandPreview(
    template: str,
    variables: list[SegmentModel],
    globalVariables: list[GlobalVariableModel]
) -> str
def moveCommand(categoryId: str, commandId: str, targetIndex: int) -> None
def runCommand(commandId: str) -> None
def saveAll() -> None
def loadAll() -> None
```

`listCommand` 返回指定分类、按 `(order, id)` 升序排列的副本或只读结果。

`moveCommand` 算法：

1. 取出 `categoryId` 下的命令并按当前 `order` 排序。
2. 校验目标命令属于该分类，且 `targetIndex` 位于 `[0, len(commands) - 1]`。
3. 从原位置移除目标命令，插入到 `targetIndex`。
4. 遍历重排结果，依次写入 `order = 0..n-1`。
5. 标记 `AppState.hasDirty = True`；不影响其他分类命令。

越界、命令不存在或分类不匹配时抛出可展示的业务错误，UI 刷新当前列表而不改变数据。

### 4.2 CategoryService / GlobalVariableService

- `CategoryService` 负责分类的新增、重命名、删除和级联清理。
- `GlobalVariableService` 负责全局变量校验、增删改查、搜索和排序。
- 任一数据写操作均标记 `hasDirty`；全局保存成功后清除该标记。

## 5. 命令构建、复制与运行

`buildCommandPreview` 的输出同时供编辑页预览、卡片预览、复制和运行使用，确保四处结果一致。

处理顺序：

1. 从模板替换 `$全局变量$`。
2. 再替换 `%命令变量%`。
3. 对包含空格或引号的参数按 Windows 规则引用和转义。
4. 未找到的全局变量保留原文；运行前阻止执行并提示。

```text
preview = replaceGlobalVariables(template, globalVariables)
preview = replaceCommandVariables(preview, variables)
return preview
```

- 编辑页和卡片的复制操作均传递最终命令文本给 `MainWindow`。
- 运行操作调用同一构建逻辑后交给 `TerminalBase.runInCmd`。
- 剪贴板失败只提示错误，不影响编辑状态和 `hasDirty`。

## 6. 交互时序

### 6.1 复制编辑页预览

1. 用户编辑模板或变量，`refreshPreview` 刷新预览并更新复制按钮状态。
2. 用户点击“复制”。
3. `CommandEditorWidget` 发出 `copyPreviewRequested(previewText)`。
4. `MainWindow` 写入系统剪贴板并展示成功或失败通知。

### 6.2 调整命令顺序

1. 用户在卡片点击“上移”或“下移”。
2. `CategoryWidget` 根据当前位置计算目标索引；边界项因按钮禁用无法触发。
3. `MainWindow` 调用 `CommandService.moveCommand`。
4. Service 重排同分类 `order` 并标记脏状态。
5. UI 刷新卡片列表和边界按钮；用户保存后顺序写入 JSON。

### 6.3 保存与恢复

1. 所有增删改和排序均更新 AppState 并标记 `hasDirty`。
2. 用户点击全局保存，`CommandService.saveAll` 调用 `JsonBase.saveToFile`。
3. 重启后 `loadAll` 读取 JSON，并按 `order` 恢复每个分类的命令顺序。

## 7. 异常与验收

提示策略：

- JSON 读取失败：提示“配置读取失败，已使用空数据”。
- 保存失败：提示原因，保留 `hasDirty`。
- 剪贴板失败：提示“复制失败”及系统错误信息。
- 排序目标非法：拒绝操作并刷新列表。
- 删除分类：确认框说明受影响的命令数量。

验收用例：

1. 编辑页预览为空时复制按钮禁用；输入有效模板后按钮启用。
2. 编辑页复制的剪贴板内容与当前预览、运行前生成的最终命令完全一致。
3. 同一分类有 3 条命令时，中间项可上移和下移；首项上移、末项下移均禁用。
4. 排序后 `commands[].order` 在该分类内连续为 `0..n-1`，其他分类不受影响。
5. 保存并重启后，命令显示顺序与排序结果一致。
6. 复制和排序不改变模板变量替换、运行、编辑、删除和全局变量功能。