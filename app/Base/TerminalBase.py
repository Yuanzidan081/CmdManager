import subprocess


class TerminalBase:
    def runInCmd(self, command: str) -> None:
        # Use a raw Windows command line to avoid converting " into \".
        subprocess.Popen(
            f"cmd /k {command}",
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )

    def runInPowerShell(self, command: str) -> None:
        # Keep command text unchanged for PowerShell as well.
        subprocess.Popen(
            f"powershell -NoExit -Command {command}",
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )

    def run(self, command: str, terminalType: str = "cmd") -> None:
        if terminalType == "powershell":
            self.runInPowerShell(command)
            return
        self.runInCmd(command)
