# CmdManager 架构说明

## 1. 定位与范围

CmdManager 是基于 PyQt6 的 Windows 桌面命令管理工具。它按分类保存命令模板、变量和值，并在界面中预览、复制或在新终端中运行最终命令。

本文只记录稳定架构、数据契约和待实现交互；控件尺寸、样式细节与完整流程见 [详细设计](./cli-generator-detailed-design.md)。

## 2. 当前能力

- 分类与命令的新增、编辑、删除、保存和加载。
- 命令模板支持命令变量 `%变量名%` 和全局变量 `$变量名$`。
- 编辑页实时生成命令预览；命令卡片展示单行省略预览和完整 tooltip。
- 命令卡片支持复制、运行、编辑、删除；运行时通过 Windows 终端执行。
- 全局变量支持维护、检索和插入模板。
- 数据持久化到 `data/commands.json`。

## 3. 分层与职责

| 层级 | 主要代码 | 职责 |
| --- | --- | --- |
| UI | `UI/MainWindow.py`、`UI/widgets/` | 展示、输入和事件转发；不直接拼接命令或读写 JSON。 |
| 服务 | `Services/` | 分类/命令/全局变量业务规则、预览构建、排序和持久化编排。 |
| 领域模型 | `Domain/` | `CategoryModel`、`CommandModel`、`SegmentModel`、`GlobalVariableModel`。 |
| 基础设施 | `Base/JsonBase.py`、`Base/TerminalBase.py` | JSON 读写及 Windows 终端启动。 |

关键边界：`CommandService` 是生成最终命令的唯一入口；UI 只展示其结果并请求复制或运行。

## 4. 核心数据契约

```json
{
  "categories": [
    { "id": "category-id", "name": "Android", "order": 0 }
  ],
  "commands": [
    {
      "id": "command-id",
      "categoryId": "category-id",
      "name": "simpleperf-record-3new",
      "description": "",
      "template": "adb shell ... %packageName%",
      "variables": [{ "key": "packageName", "value": "com.example.app" }],
      "order": 0
    }
  ],
  "globalVariables": [
    { "key": "SDK_ROOT", "value": "E:\\sdk", "description": "Android SDK 路径" }
  ]
}
```

- `id` 全局唯一；`categoryId` 必须指向现存分类。
- `order` 只在同一分类的命令间比较，排序后必须从 `0` 起连续。
- 删除分类时级联删除其命令。
- 渲染顺序：先替换 `$全局变量$`，再替换 `%命令变量%`。

## 5. 本次待实现交互

### 5.1 编辑页命令预览复制

在 `CommandEditorWidget` 的“命令预览”标题右侧增加“复制”按钮。

- 点击后复制当前预览文本到系统剪贴板，复制内容必须与运行时使用的最终命令一致。
- 预览为空时按钮禁用；复制成功后通过现有通知机制提示“已复制命令”。
- 按钮仅复制，不保存、不执行，也不修改模板或变量。
- 复制逻辑由 `MainWindow` 或注入的回调统一处理，避免 Widget 直接承载业务规则。

### 5.2 命令上下调整顺序

在每张 `CommandCardWidget` 上提供“上移”和“下移”操作，位于现有操作区且不影响复制、运行、编辑、删除。

- 上移/下移仅在当前分类内交换相邻命令的位置。
- 首项禁用“上移”，末项禁用“下移”；分类内只有一条命令时两者均禁用。
- 操作后立即重排列表并更新相关命令的连续 `order` 值；状态沿用现有保存策略写入 JSON。
- 服务层提供 `moveCommand(categoryId, commandId, targetIndex)`，UI 不直接修改 `order`。

## 6. 验收

1. 编辑页预览右侧可复制，剪贴板内容与当前预览/运行命令完全一致。
2. 命令可逐项上移、下移；边界按钮正确禁用。
3. 调整顺序后切换分类、重启应用，命令顺序保持不变。
4. 复制和排序不改变模板变量替换、编辑、运行和删除的既有行为。