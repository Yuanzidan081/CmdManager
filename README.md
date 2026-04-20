# CmdManager

CmdManager 是一个基于 PyQt6 的桌面命令管理工具，用于把常用命令按分类集中管理，并通过图形界面快速运行。图形界面参考了CC-Switch界面的布局。

## 功能概览

- 分类管理
  - 支持新增、重命名、删除分类。
  - 分类以 Tab 形式展示。
- 命令管理
  - 每个分类下可新增、编辑、删除命令。
  - 命令使用卡片展示：名称、描述、预览、运行/编辑/删除按钮。
- 命令片段编辑
  - 命令由多个片段组成，支持 `literal` 与 `variable` 两种类型。
  - 支持片段新增、删除、上移、下移。
- 命令预览与执行
  - 编辑时实时预览最终命令。
  - 点击运行后，在新开的 cmd 窗口执行命令。
- 数据持久化
  - 数据保存到 `data/commands.json`。
  - 支持手动保存；关闭窗口时若有未保存变更会自动尝试保存。

## 环境要求

- 操作系统：Windows（当前终端启动逻辑为 Windows 命令）
- Python：建议 3.9+
- 依赖：PyQt6（见 `requirements.txt`）

## 安装步骤

在项目根目录执行以下命令。

### 1) 创建虚拟环境

```powershell
python -m venv .venv
```

### 2) 激活虚拟环境

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

CMD:

```bat
.venv\Scripts\activate.bat
```

### 3) 安装依赖

```powershell
pip install -r requirements.txt
```

## 运行方式

在项目根目录执行：

```powershell
python app/main.py
```

程序启动后会自动加载 `data/commands.json`。如果当前数据为空，会自动创建一个默认分类 `常用`。

## 快速使用

1. 在顶部输入框输入分类名，点击“新增分类”。
2. 进入分类后点击“新增命令”。
3. 在编辑页填写命令名称、描述，并添加命令片段。
4. 点击“保存”返回列表页。
5. 在命令卡片点击“运行”，将在新 cmd 窗口执行。
6. 点击顶部“保存”将当前状态写入 `data/commands.json`。

## 项目结构

```text
CmdManager/
├─ requirements.txt
├─ README.md
├─ app/
│  ├─ main.py
│  ├─ Base/
│  │  ├─ JsonBase.py
│  │  └─ TerminalBase.py
│  ├─ Domain/
│  │  ├─ AppState.py
│  │  ├─ CategoryModel.py
│  │  ├─ CommandModel.py
│  │  └─ SegmentModel.py
│  ├─ Services/
│  │  ├─ CategoryService.py
│  │  └─ CommandService.py
│  └─ UI/
│     ├─ MainWindow.py
│     ├─ styles/
│     │  └─ theme.qss
│     └─ widgets/
│        ├─ CategoryWidget.py
│        ├─ CommandCardWidget.py
│        ├─ CommandEditorWidget.py
│        └─ SegmentWidget.py
├─ data/
│  └─ commands.json
└─ Docs/
   ├─ cli-generator-architecture.md
   ├─ cli-generator-detailed-design.md
   └─ images/
      ├─ widget-main.png
      └─ widget-commandedit.png
```

## 数据文件说明

`data/commands.json` 结构示例：

```json
{
  "categories": [
    {
      "id": "category-id",
      "name": "分类名",
      "order": 0
    }
  ],
  "commands": [
    {
      "id": "command-id",
      "categoryId": "category-id",
      "name": "命令名",
      "description": "命令描述",
      "segments": [
        {
          "type": "literal",
          "value": "echo"
        },
        {
          "type": "variable",
          "value": "hello"
        }
      ],
      "order": 0
    }
  ]
}
```

## 当前限制

- “导入 / 导出 / 设置”按钮目前为占位提示，尚未实现具体功能。
- `variable` 片段当前用于建模与编辑，运行时不会弹窗输入参数，使用的是已保存值。
- UI 运行命令默认走 cmd；底层已预留 PowerShell 运行方法，可后续接入界面选项。

## 相关文档

- 架构设计：`Docs/cli-generator-architecture.md`
- 详细设计：`Docs/cli-generator-detailed-design.md`
