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
  - 全局按钮：新增分类、保存、导入、导出、设置
- Tab 区域
  - 展示全部分类
  - 支持切换、重命名、删除
- 内容区域
  - 使用 QStackedWidget 承载两种页面
    - CommandListPage（命令卡片列表）
    - CommandEditorPage（命令编辑页）

切换规则：

1. 进入应用默认显示 CommandListPage。
2. 点击命令卡片的编辑按钮，切换到 CommandEditorPage。
3. 点击编辑页返回按钮，切回 CommandListPage。

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
2. description
3. commandPreview（由 CommandService 动态生成）

展示规则：

1. commandPreview 使用单行省略策略，超出宽度显示 `...`。
2. 鼠标悬停 commandPreview 时显示完整命令 tooltip。
3. 运行/编辑/删除按钮固定在右侧，始终可见。

按钮：

1. run
2. edit
3. remove

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

## 2.5 SegmentWidget

变量输入模式：

1. key 来自模板占位符，使用 label 展示。
2. value 使用 lineEdit 输入。
3. 输入项由模板自动增减，不再区分分段类型。

## 2.6 视觉参数建议（对齐 CC 风格）

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
7. buildCommandPreview(template: str, variables: list[SegmentModel]) -> str
8. runCommand(commandId: str) -> None
9. saveAll() -> None
10. loadAll() -> None

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
  "commands": []
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
    selectedCategoryId: str | None
    editingCommandId: str | None
    hasDirty: bool
```

状态更新原则：

1. 所有写操作通过 Service。
2. Service 更新 AppState 后通知 UI 刷新。
3. hasDirty 仅在数据变更后置为 True，保存后归零。

## 7. 命令拼接与转义算法

输入：template, variables

输出：可执行命令字符串

算法：

1. 解析 template 中的 `%变量名%`。
2. 根据变量名匹配 variables 中的 value。
3. 用 value 替换 template 中的 `%变量名%`。
4. 对替换后的参数按平台规则做引号和转义处理。

伪代码：

```text
preview = template
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

## 8. 页面交互时序

## 8.1 编辑并保存命令

1. 用户进入编辑页。
2. 修改 name、description、template。
3. 系统根据 template 自动生成变量输入项，用户填写 variables。
4. 点击保存。
5. CommandService.updateCommand。
6. hasDirty = True。
7. 用户点击全局保存。
8. CommandService.saveAll 调用 JsonBase.saveToFile。
9. hasDirty = False。

## 8.2 运行命令

1. 用户点击 run。
2. CommandService.buildCommandPreview。
3. CommandService.runCommand。
4. TerminalBase.runInCmd。

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

## 10. 异常与提示策略

1. JSON 读取失败：顶部提示“配置读取失败，已使用空数据”。
2. 保存失败：提示错误原因，不清理 hasDirty。
3. 运行失败：提示命令内容与错误码。
4. 删除分类：确认框显示受影响命令数量。

## 11. Phase 1 开发任务拆分

1. 搭建目录与空类文件。
2. 完成 Domain + JsonBase。
3. 完成 CategoryService + CommandService 基础能力。
4. 完成 MainWindow + CategoryWidget + CommandCardWidget。
5. 完成 CommandEditorWidget + SegmentWidget。
6. 接入 TerminalBase 运行能力。
7. 接入保存按钮与 hasDirty 状态。
8. 联调并完成验收测试。

## 12. 验收用例

1. 新增 3 个分类并重启，分类仍存在。
2. 每个分类新增至少 1 个命令并保存成功。
3. 命令模板包含 `%appName%`、`%version%` 时，可自动生成输入项并正确替换预览。
4. 点击 run，可在新 cmd 窗口看到执行。
5. 删除分类后，其命令不再出现在 JSON。
