import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from Base.JsonBase import JsonBase
from Base.TerminalBase import TerminalBase
from Domain.AppState import AppState
from Services.CategoryService import CategoryService
from Services.CommandService import CommandService
from UI.MainWindow import MainWindow


def loadTheme(themePath: str) -> str:
    path = Path(themePath)
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def main() -> int:
    app = QApplication(sys.argv)

    rootPath = Path(__file__).resolve().parents[1]
    dataFilePath = rootPath / "data" / "commands.json"
    themePath = rootPath / "app" / "UI" / "styles" / "theme.qss"

    jsonBase = JsonBase()
    terminalBase = TerminalBase()
    appState = AppState()

    categoryService = CategoryService(appState)
    commandService = CommandService(
        appState,
        jsonBase,
        terminalBase,
        str(dataFilePath),
    )

    commandService.loadAll()
    if not appState.categoryList:
        categoryService.addCategory("常用")
        commandService.saveAll()
        appState.hasDirty = False

    styleSheet = loadTheme(str(themePath))
    if styleSheet:
        app.setStyleSheet(styleSheet)

    mainWindow = MainWindow(appState, categoryService, commandService)
    mainWindow.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
