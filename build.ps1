param(
    [switch]$SkipPipUpgrade
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptRoot

function Resolve-PythonCommand {
    $candidateList = @(
        @{ command = "py"; args = @("-3") },
        @{ command = "python"; args = @() }
    )

    foreach ($candidate in $candidateList) {
        $cmd = Get-Command $candidate.command -ErrorAction SilentlyContinue
        if ($null -ne $cmd) {
            return $candidate
        }
    }

    throw "Python 3 not found. Install Python and ensure py or python is available."
}

function Invoke-PythonCommand {
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$Python,

        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    & $Python.command @($Python.args + $Arguments)
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed: $($Python.command) $($Python.args -join ' ') $($Arguments -join ' ')"
    }
}

$python = Resolve-PythonCommand
Write-Host "Using Python: $($python.command) $($python.args -join ' ')"

if (-not $SkipPipUpgrade) {
    Invoke-PythonCommand -Python $python -Arguments @("-m", "pip", "install", "--upgrade", "pip")
}

Invoke-PythonCommand -Python $python -Arguments @("-m", "pip", "install", "-r", "requirements.txt")
Invoke-PythonCommand -Python $python -Arguments @("-m", "pip", "install", "pyinstaller")

$distPath = Join-Path $scriptRoot "build"
$tempPath = Join-Path $scriptRoot ".pyinstaller"
$workPath = Join-Path $tempPath "work"
$specPath = Join-Path $tempPath "spec"
$entryScriptPath = Join-Path $scriptRoot "app\main.py"
$themeSourcePath = Join-Path $scriptRoot "app\UI\styles\theme.qss"

if (-not (Test-Path $entryScriptPath)) {
    throw "Entry script not found: $entryScriptPath"
}
if (-not (Test-Path $themeSourcePath)) {
    throw "Theme file not found: $themeSourcePath"
}

if (Test-Path $distPath) {
    Remove-Item -Path $distPath -Recurse -Force
}
if (Test-Path $tempPath) {
    Remove-Item -Path $tempPath -Recurse -Force
}

New-Item -ItemType Directory -Path $distPath | Out-Null
New-Item -ItemType Directory -Path $tempPath | Out-Null

Invoke-PythonCommand -Python $python -Arguments @(
    "-m", "PyInstaller",
    "--noconfirm",
    "--clean",
    "--windowed",
    "--onefile",
    "--name", "CmdManager",
    "--distpath", $distPath,
    "--workpath", $workPath,
    "--specpath", $specPath,
    "--add-data", "$themeSourcePath;app/UI/styles",
    "--collect-all", "PyQt6",
    $entryScriptPath
)

if (Test-Path $tempPath) {
    Remove-Item -Path $tempPath -Recurse -Force
}

$exePath = Join-Path $distPath "CmdManager.exe"
if (-not (Test-Path $exePath)) {
    throw "Build finished, but output file is missing: $exePath"
}

Write-Host "Build completed: $exePath"
Write-Host "Double-click the exe to run. Data file location: $(Join-Path $distPath 'data\\commands.json')"
