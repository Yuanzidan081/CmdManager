# 命令行脚本生成工具详细设计

## 1. 设计目标

在现有架构方案基础上，给出可直接编码的详细设计，确保以下点可落地：

1. UI 结构固定，交互路径明确。
2. 领域模型字段稳定，JSON 可双向映射。
3. 服务层方法边界清晰，UI 不直接处理业务。
4. 命令拼接和转义逻辑单点收敛。
5. 支持后续扩展变量校验策略和多平台运行。

## 2. UI 详细设计

## 2.1 MainWindow 结构

- 顶栏区域
  - 应用标题
  - 全局按钮：新增分类、重命名分类、删除分类、保存、设置
- Tab 区域
  - 展示全部分类
  - 支持切换、重命名、删除
- 内容区域
  - 使用 QStackedWidget 承载三种页面
    - CommandListPage（命令卡片列表）
    - CommandEditorPage（命令编辑页）
    - SettingsPage（设置页，当前为全局变量管理）

切换规则：

1. 进入应用默认显示 CommandListPage。
2. 点击命令卡片的编辑按钮，切换到 CommandEditorPage。
3. 点击编辑页返回按钮，切回 CommandListPage。
4. 点击顶部设置按钮，切换到 SettingsPage。
5. 点击设置页返回按钮，切回 CommandListPage。

## 2.2 CategoryWidget

职责：分类展示与管理。

交互：

1. 新增分类：输入名称后创建，自动切换到新分类。
2. 重命名分类：名称去重校验。
3. 删除分类：二次确认，删除时级联删除其命令。
4. 调整顺序：支持拖拽排序，更新 order。

滚动策略：

1. 命令列表仅允许纵向滚动，不显示横向滚动条。
2. 命令列表 ScrollArea 的右侧滚动条使用扁平样式，不允许出现系统默认凸起效果。

## 2.3 CommandCardWidget

职责：单条命令展示。

字段展示：

1. name
2. commandPreview（由 CommandService 动态生成，位于 name 下方）

展示规则：

1. commandPreview 使用 QLabel（非 lineEdit）显示，样式为透明无边框。
2. commandPreview 使用单行省略策略，超出宽度显示 `...`。
3. commandPreview 显示宽度固定为预设值（当前 620）。
4. 鼠标悬停卡片时显示完整命令 tooltip。
5. 按钮固定在右侧，窗口横向拉伸时按钮不拉伸。
6. 窗口横向拉伸时，仅中间 stretch 区域变化，文本区与按钮区间距随之变化。

按钮：

1. copy（第一个）
2. run
3. edit
4. remove

## 2.4 CommandEditorWidget

布局：

1. 顶部固定区：返回按钮 + 标题。
2. 中部滚动区：命令基础信息（name、description、template）、变量输入列表、命令预览。
3. 底部固定区：保存按钮。
4. 中部仅使用一个外层 ScrollView，不使用嵌套内层 ScrollView。
5. 中部 ScrollArea 右侧滚动条使用扁平样式，不允许出现系统默认凸起效果。

编辑规则：

1. template 不能为空。
2. `%变量名%` 由模板自动解析并去重。
3. 每个变量都需要填写 value。
4. 不再手动新增分段类型。
5. 滚动中返回和保存按钮保持可见，不随内容滚动。
6. 模板输入区提供“插入全局变量”按钮，用于打开全局变量选择弹层。
7. 选择弹层确认后，按 `$变量名$` 格式插入到模板输入框当前光标位置。

## 2.5 SegmentWidget

变量输入模式：

1. key 来自模板占位符，使用 label 展示。
2. value 使用 lineEdit 输入。
3. 输入项由模板自动增减，不再区分分段类型。

## 2.6 SettingsWidget / GlobalVarWidget

职责：全局变量管理与检索。

布局：

1. 顶部固定区：返回按钮 + 标题（设置 / 全局变量）。
2. 工具区：搜索框、排序按钮（名称升序/降序）、新增按钮。
3. 中部列表区：可滚动变量列表，每项显示 key、value。
4. 底部固定区：保存按钮。

交互规则：

1. 支持新增、编辑、删除全局变量。
2. 支持按 key 实时搜索过滤。
3. 支持滚动浏览大量变量。
4. key 不能为空且在全局变量集合内唯一。
5. 保存后写回 `globalVariables` 字段。

## 2.7 GlobalVarPickerWidget

职责：在命令编辑过程中快速检索并插入全局变量（交互参考 Unity Add Component）。

布局：

1. 顶部：搜索输入框。
2. 中部：可滚动候选列表。
3. 底部：添加按钮。

交互规则：

1. 打开时默认展示全部变量。
2. 输入关键字后按 key 实时模糊过滤。
3. 鼠标悬停列表项显示 tooltip（key、value）。
4. 单击选中后点击“添加”，或双击/回车，插入 `$变量名$`。
5. 支持 Esc 关闭，关闭后焦点回到模板输入框。

## 2.8 视觉参数建议（对齐 CC 风格）

1. 主背景：#f3f4f6
2. 卡片背景：#ffffff
3. 主强调色：#ff7a00
4. 圆角：12
5. 主按钮高度：34
6. 卡片内边距：16
7. 列表项间距：12
8. 编辑页滚动区：扁平样式，无凸起边框
9. ScrollBar 样式：对 QScrollBar 采用全局扁平定义（groove 透明、arrow 隐藏、corner 透明）

## 3. 领域模型详细定义

```python
from dataclasses import dataclass, field
from typing import List


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
    variables: List[SegmentModel] = field(default_factory=list)
    order: int = 0


@dataclass
class CategoryModel:
    id: str
    name: str
    order: int = 0
```

约束：

1. id 全局唯一（推荐 uuid4 字符串）。
2. order 在同级内唯一且连续。
3. 删除 Category 时，同步删除关联 Command。
4. GlobalVariableModel.key 在全局变量集合内唯一。

## 4. 服务层接口设计

## 4.1 CategoryService

建议方法：

1. addCategory(name: str) -> CategoryModel
2. renameCategory(categoryId: str, newName: str) -> None
3. removeCategory(categoryId: str) -> None
4. moveCategory(categoryId: str, targetIndex: int) -> None
5. listCategory() -> list[CategoryModel]

业务规则：

1. 分类名不能为空。
2. 分类名在当前数据集中唯一。
3. removeCategory 执行级联删除命令。

## 4.2 CommandService

建议方法：

1. addCommand(categoryId: str, name: str, description: str, template: str, variables: list[SegmentModel]) -> CommandModel
2. updateCommand(commandId: str, name: str, description: str, template: str, variables: list[SegmentModel]) -> None
3. removeCommand(commandId: str) -> None
4. moveCommand(categoryId: str, commandId: str, targetIndex: int) -> None
5. listCommand(categoryId: str) -> list[CommandModel]
6. parseTemplateVariables(template: str) -> list[str]
7. buildCommandPreview(template: str, variables: list[SegmentModel], globalVariables: list[GlobalVariableModel]) -> str
8. runCommand(commandId: str) -> None
9. saveAll() -> None
10. loadAll() -> None

业务规则：

1. 命令预览/执行前先替换 `$变量名$`，后替换 `%变量名%`。
2. 未找到的 `$变量名$` 保留原文并给出提示。

## 4.3 GlobalVariableService

建议方法：

1. addGlobalVariable(key: str, value: str) -> GlobalVariableModel
2. updateGlobalVariable(key: str, value: str) -> None
3. removeGlobalVariable(key: str) -> None
4. listGlobalVariable() -> list[GlobalVariableModel]
5. searchGlobalVariable(keyword: str) -> list[GlobalVariableModel]
6. sortGlobalVariable(ascending: bool = True) -> list[GlobalVariableModel]

业务规则：

1. key 不能为空且唯一。
2. key 建议使用大写字母、数字和下划线。
3. searchGlobalVariable 仅负责数据过滤，不直接处理 UI 状态。

## 5. 基础设施详细设计

## 5.1 JsonBase

建议方法：

1. loadFromFile(path: str) -> dict
2. saveToFile(path: str, data: dict) -> None
3. ensureDataFile(path: str) -> None

策略：

1. 启动时确保 data/commands.json 存在。
2. 保存使用覆盖写入（手动保存触发）。
3. 读取失败时回退到空结构。

空结构：

```json
{
  "categories": [],
  "commands": [],
  "globalVariables": []
}
```

## 5.2 TerminalBase

建议方法：

1. runInCmd(command: str) -> None
2. runInPowerShell(command: str) -> None
3. run(command: str, terminalType: str = "cmd") -> None

Windows 命令：

1. cmd: start cmd /k "{command}"
2. powershell: start powershell -NoExit -Command "{command}"

## 6. 状态模型设计

集中状态对象 AppState：

```python
@dataclass
class AppState:
    categoryList: list[CategoryModel]
    commandList: list[CommandModel]
    globalVariableList: list[GlobalVariableModel]
    selectedCategoryId: str | None
    editingCommandId: str | None
    isSettingsPage: bool
    hasDirty: bool
```

状态更新原则：

1. 所有写操作通过 Service。
2. Service 更新 AppState 后通知 UI 刷新。
3. hasDirty 仅在数据变更后置为 True，保存后归零。

## 7. 命令拼接与转义算法

输入：template, variables, globalVariables

输出：可执行命令字符串

算法：

1. 解析 template 中的 `$变量名$`。
2. 根据变量名匹配 globalVariables 中的 value，并完成替换。
3. 解析 template 中的 `%变量名%`。
4. 根据变量名匹配 variables 中的 value，并完成替换。
5. 对替换后的参数按平台规则做引号和转义处理。

伪代码：

```text
preview = template
for globalVariable in globalVariables:
  key = "$" + globalVariable.key + "$"
  preview = replaceAll(preview, key, trim(globalVariable.value))
for variable in variables:
    key = "%" + variable.key + "%"
    value = quoteIfNeed(trim(variable.value))
    preview = replaceAll(preview, key, value)
return preview
```

quoteIfNeed 规则（Windows）：

1. 无空格、无双引号时原样返回。
2. 有空格时加双引号。
3. 内含双引号时转义后再包裹。

占位符匹配建议：

1. 模板变量：`%([A-Za-z0-9]+)%`
2. 全局变量：`\$([A-Za-z0-9_]+)\$`
3. 替换时使用正则分组，避免对普通文本中的 `%`、`$` 误替换。

## 8. 页面交互时序

## 8.1 编辑并保存命令

1. 用户进入编辑页。
2. 修改 name、description、template。
3. 如需插入全局变量，点击“插入全局变量”打开 GlobalVarPickerWidget。
4. 在弹层搜索、滚动、悬停查看 tooltip，确认后插入 `$变量名$`。
5. 系统根据 template 自动生成变量输入项，用户填写 variables。
6. 点击保存。
7. CommandService.updateCommand。
8. hasDirty = True。
9. 用户点击全局保存。
10. CommandService.saveAll 调用 JsonBase.saveToFile。
11. hasDirty = False。

## 8.2 运行命令

1. 用户点击 run。
2. CommandService.buildCommandPreview。
3. CommandService.runCommand。
4. TerminalBase.runInCmd。

## 8.3 管理全局变量

1. 用户点击顶部“设置”按钮进入 SettingsPage。
2. 在 GlobalVarWidget 中新增/编辑/删除变量。
3. 使用搜索框快速过滤变量列表。
4. 点击保存。
5. GlobalVariableService 更新 AppState.globalVariableList。
6. CommandService.saveAll 调用 JsonBase.saveToFile。

## 9. JSON 映射规则

映射关系：

1. CategoryModel.id -> categories[].id
2. CategoryModel.name -> categories[].name
3. CategoryModel.order -> categories[].order
4. CommandModel.id -> commands[].id
5. CommandModel.categoryId -> commands[].categoryId
6. CommandModel.name -> commands[].name
7. CommandModel.description -> commands[].description
8. CommandModel.template -> commands[].template
9. CommandModel.order -> commands[].order
10. SegmentModel.key -> commands[].variables[].key
11. SegmentModel.value -> commands[].variables[].value
12. GlobalVariableModel.key -> globalVariables[].key
13. GlobalVariableModel.value -> globalVariables[].value

## 10. 异常与提示策略

1. JSON 读取失败：顶部提示“配置读取失败，已使用空数据”。
2. 保存失败：提示错误原因，不清理 hasDirty。
3. 运行失败：提示命令内容与错误码。
4. 删除分类：确认框显示受影响命令数量。
5. 插入全局变量失败（变量不存在）：提示“变量不存在或已删除”，并保留模板原文。

## 11. Phase 1 开发任务拆分

1. 搭建目录与空类文件。
2. 完成 Domain + JsonBase。
3. 完成 CategoryService + CommandService 基础能力。
4. 完成 MainWindow + CategoryWidget + CommandCardWidget。
5. 完成 CommandEditorWidget + SegmentWidget。
6. 完成 SettingsWidget + GlobalVarWidget + GlobalVarPickerWidget。
7. 接入 GlobalVariableService 与 `globalVariables` 持久化。
8. 接入 TerminalBase 运行能力。
9. 接入保存按钮与 hasDirty 状态。
10. 联调并完成验收测试。

## 12. 验收用例

1. 新增 3 个分类并重启，分类仍存在。
2. 每个分类新增至少 1 个命令并保存成功。
3. 命令模板包含 `%appName%`、`%version%` 时，可自动生成输入项并正确替换预览。
4. 点击 run，可在新 cmd 窗口看到执行。
5. 删除分类后，其命令不再出现在 JSON。
6. 在命令编辑页可通过“插入全局变量”弹层检索变量，支持搜索、滚动、tooltip，并正确插入 `$变量名$`。
7. 模板同时包含 `$变量名$` 与 `%变量名%` 时，预览与执行结果替换正确。

## 13. 文件级落地设计

建议新增或完善以下文件：

1. `app/UI/widgets/SettingsWidget.py`
2. `app/UI/widgets/GlobalVarWidget.py`
3. `app/UI/widgets/GlobalVarPickerWidget.py`
4. `app/Services/GlobalVariableService.py`
5. `app/Domain/GlobalVariableModel.py`

现有文件建议补充：

1. `app/UI/MainWindow.py`：增加 SettingsPage 切换与返回绑定。
2. `app/UI/widgets/CommandEditorWidget.py`：增加“插入全局变量”按钮与插入动作。
3. `app/Services/CommandService.py`：补充 `$变量名$` + `%变量名%` 双阶段渲染。
4. `app/Base/JsonBase.py`：读写 `globalVariables` 字段并兼容旧数据。

## 14. 关键接口与信号约定

## 14.1 MainWindow

建议方法：

1. showCommandListPage() -> None
2. showCommandEditorPage(commandId: str | None) -> None
3. showSettingsPage() -> None
4. onSettingsBack() -> None

## 14.2 CommandEditorWidget

建议方法：

1. setCommandData(command: CommandModel | None) -> None
2. onInsertGlobalVariableClick() -> None
3. insertTextAtCursor(text: str) -> None
4. rebuildSegmentInputs(template: str) -> None
5. refreshPreview() -> None

信号建议：

1. saveRequested(commandPayload: dict)
2. backRequested()

## 14.3 GlobalVarPickerWidget

建议方法：

1. setData(globalVariables: list[GlobalVariableModel]) -> None
2. setKeyword(keyword: str) -> None
3. getSelected() -> GlobalVariableModel | None

信号建议：

1. variablePicked(key: str)
2. closed()

## 14.4 GlobalVariableService

建议方法：

1. validateKey(key: str) -> None
2. findByKey(key: str) -> GlobalVariableModel | None
3. upsertGlobalVariable(item: GlobalVariableModel) -> None

## 15. 具体交互流程（可直接实现）

## 15.1 插入全局变量

1. `CommandEditorWidget.onInsertGlobalVariableClick` 打开 `GlobalVarPickerWidget`。
2. `GlobalVarPickerWidget` 初始化时调用 `GlobalVariableService.listGlobalVariable`。
3. 用户输入关键字时，触发 `searchGlobalVariable` 更新列表。
4. 用户确认后发出 `variablePicked(key)`。
5. `CommandEditorWidget` 收到信号后插入 `$key$`，随后调用 `refreshPreview`。

## 15.2 保存设置页全局变量

1. `GlobalVarWidget` 编辑完成后提交列表草稿。
2. `GlobalVariableService` 执行 key 唯一性校验。
3. 校验通过后更新 `AppState.globalVariableList` 并标记 `hasDirty = True`。
4. 用户点击全局保存时，`CommandService.saveAll` 一并落盘 `globalVariables`。

## 16. 兼容性与迁移策略

1. 读取旧版 JSON 时，若无 `globalVariables` 字段，自动填充为空数组。
2. 写回时始终输出 `globalVariables` 字段，避免版本间行为不一致。
3. 如果模板中引用了不存在的 `$变量名$`，预览保留原文，运行前弹出错误提示并阻止执行。
