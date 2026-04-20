import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from Base.JsonBase import JsonBase
from Base.TerminalBase import TerminalBase
from Domain.AppState import AppState
from Services.CategoryService import CategoryService
from Services.CommandService import CommandService
from UI.MainWindow import MainWindow


def getAppRootPath() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def getResourceRootPath() -> Path:
    if getattr(sys, "frozen", False):
        meipassPath = getattr(sys, "_MEIPASS", "")
        if meipassPath:
            return Path(meipassPath)
    return getAppRootPath()


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

    appRootPath = getAppRootPath()
    resourceRootPath = getResourceRootPath()

    dataFilePath = appRootPath / "data" / "commands.json"
    themePath = resourceRootPath / "app" / "UI" / "styles" / "theme.qss"

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
