# CmdManager

CmdManager 是一个基于 PyQt6 的桌面命令管理工具，用于把常用命令按分类集中管理，并通过图形界面快速运行。图形界面参考了CC-Switch界面的布局。

## 核心能力

- 分类管理
  - 支持新增、重命名、删除、排序分类。
  - 分类以 Tab 形式展示。
- 命令管理
  - 每个分类下可新增、编辑、删除、排序命令。
  - 长命令预览使用单行省略显示（末尾 `...`），悬停卡片可查看完整命令提示。
  - 命令卡片按钮为“复制、运行、编辑、删除”。
- 模板变量驱动
  - 命令由 template 定义，使用 `%变量名%` 作为占位符。
  - 编辑器会自动解析模板变量并生成输入项，不再手动维护分段类型。
- 命令预览与执行
  - 预览区实时展示替换后的命令。
  - 点击运行后在新的终端窗口执行最终命令。
- 数据持久化
  - 数据保存到 `data/commands.json`。
  - 启动时自动加载；通过“保存”按钮覆盖写入。
 
## 分层架构

- UI 层
  - MainWindow、CategoryWidget、CommandCardWidget、CommandEditorWidget、SegmentWidget。
- 服务层
  - CategoryService：分类新增、重命名、删除、排序。
  - CommandService：命令增删改、模板解析、预览构建、运行、保存、加载。
- 领域模型层
  - CategoryModel：id、name、order。
  - CommandModel：id、categoryId、name、description、template、variables、order。
  - SegmentModel：key、value。
- 基础设施层
  - JsonBase：JSON 文件创建、读取、写入。
  - TerminalBase：cmd / PowerShell 启动与运行。

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

程序启动后会自动加载 `data/commands.json`。
若数据文件不存在，会自动创建空结构：

```json
{
  "categories": [],
  "commands": []
}
```

## 快速使用

1. 在顶部输入框输入分类名，点击“新增分类”。
2. 进入分类后点击“新增命令”。
3. 在编辑页填写 name、description、template（例如：`E:\unity\build.bat %appName% %version%`）。
4. 根据自动生成的变量输入项填写 value。
5. 点击“保存”返回列表页。
6. 点击顶部“保存”将当前状态写入 `data/commands.json`。
7. 在命令卡片点击“运行”，将在新终端窗口执行最终命令。

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
      "template": "E:\\unity\\build.bat %appName% %version%",
      "variables": [
        {
          "key": "appName",
          "value": "DemoGame"
        },
        {
          "key": "version",
          "value": "1.2.3"
        }
      ],
      "order": 0
    }
  ]
}
```

## 命令拼接与转义

- CommandService 负责模板变量替换和预览拼接，UI 不直接拼接命令字符串。
- Windows 下的 quoteIfNeed 规则：
  - 无空格且无双引号：原样返回。
  - 含空格：自动加双引号。
  - 含双引号：先转义再包裹双引号。

Windows 终端运行策略：

- cmd：`start cmd /k "{command}"`
- PowerShell：`start powershell -NoExit -Command "{command}"`

## 当前限制

- 顶部工具栏仅保留“新增分类 / 重命名分类 / 删除分类 / 保存 / 设置”，导入与导出入口已移除。
- “设置”按钮目前为占位提示，尚未实现具体功能。
- UI 运行命令默认走 cmd；底层已预留 PowerShell 运行方法，可后续接入界面选项。

## 打包为 EXE

在项目根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

脚本会自动完成以下步骤：

1. 安装 `requirements.txt` 里的依赖。
2. 自动安装 `pyinstaller`。
3. 生成单文件可执行程序到 `build/CmdManager.exe`。

说明：

- 双击 `build/CmdManager.exe` 可直接运行。
- 运行时数据文件会自动写入 `build/data/commands.json`。

## 相关文档

- 架构设计：`Docs/cli-generator-architecture.md`
- 详细设计：`Docs/cli-generator-detailed-design.md`
