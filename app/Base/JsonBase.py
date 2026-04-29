import json
from pathlib import Path


class JsonBase:
    def getDefaultData(self) -> dict:
        return {
            "categories": [],
            "commands": [],
            "globalVariables": [],
        }

    def ensureDataFile(self, path: str) -> None:
        filePath = Path(path)
        filePath.parent.mkdir(parents=True, exist_ok=True)
        if not filePath.exists():
            self.saveToFile(path, self.getDefaultData())

    def loadFromFile(self, path: str) -> dict:
        self.ensureDataFile(path)
        filePath = Path(path)
        try:
            text = filePath.read_text(encoding="utf-8")
            data = json.loads(text)
            if isinstance(data, dict):
                defaultData = self.getDefaultData()
                for key, value in defaultData.items():
                    if key not in data or not isinstance(data[key], list):
                        data[key] = value
                return data
        except Exception:
            return self.getDefaultData()
        return self.getDefaultData()

    def saveToFile(self, path: str, data: dict) -> None:
        filePath = Path(path)
        filePath.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(data, indent=2, ensure_ascii=False)
        filePath.write_text(text, encoding="utf-8")
