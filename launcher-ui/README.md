# Launcher UI (single start entry)

## Start (PowerShell only)
```powershell
Set-Location "E:\文档\New project"
.\start-ui.ps1
```

This script will:
- set npm/electron mirror
- install dependencies if missing
- start desktop mode, fallback to web mode
