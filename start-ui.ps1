$ErrorActionPreference = 'Stop'
Set-Location -Path "$PSScriptRoot\launcher-ui"

$env:ELECTRON_MIRROR = 'https://npmmirror.com/mirrors/electron/'
$env:ELECTRON_BUILDER_BINARIES_MIRROR = 'https://npmmirror.com/mirrors/electron-builder-binaries/'
$env:npm_config_registry = 'https://registry.npmmirror.com/'

if (-not (Test-Path node_modules)) {
  Write-Host '[INFO] Installing npm dependencies mirror enabled...'
  try {
    npm install
  } catch {
    Write-Host '[WARN] First install failed, retrying...'
    try {
      npm install
    } catch {
      Write-Host '[WARN] Desktop dependencies still failed. Trying minimal web dependencies...'
      npm install --no-optional
    }
  }
}

try {
  Write-Host '[INFO] Starting launcher UI...'
  npm run dev
} catch {
  Write-Host '[WARN] Desktop mode failed, fallback to web mode.'
  npm run dev:web
}
