const { app, BrowserWindow, ipcMain } = require('electron')
const path = require('node:path')
const fs = require('node:fs')
const { spawnSync } = require('node:child_process')

const isDev = !app.isPackaged

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 760,
    minWidth: 1024,
    minHeight: 640,
    frame: false,
    backgroundColor: '#0f1220',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  })

  if (isDev) {
    win.loadURL('http://127.0.0.1:5173')
  } else {
    win.loadFile(path.join(__dirname, '../dist/index.html'))
  }
}

const registryDetectMap = {
  nz_future: { displayName: 'NZM launcher', valueName: 'InstallSource', exeName: 'nzm_launcher.exe' },
  delta_force: { displayName: 'DF Launcher', valueName: 'InstallSource', exeName: 'delta_force_launcher.exe' },
  wuthering_waves: { displayName: 'KRInstall Wuthering Waves', valueName: 'InstallPath', exeName: 'launcher.exe' }
}

function runPowerShellJson(script) {
  const wrapped = `[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; ${script}`
  const result = spawnSync('powershell', ['-NoProfile', '-NonInteractive', '-Command', wrapped], {
    encoding: 'utf8'
  })

  if (result.status !== 0) {
    return { ok: false, value: null, error: result.stderr || result.stdout || 'powershell-failed' }
  }

  const text = (result.stdout || '').trim()
  if (!text) return { ok: true, value: null, error: '' }

  try {
    return { ok: true, value: JSON.parse(text), error: '' }
  } catch (e) {
    return { ok: false, value: null, error: `json-parse-failed: ${String(e)}` }
  }
}

function findUninstallEntry(displayName) {
  const escapedName = displayName.replace(/'/g, "''")
  const script = `
    $base = 'HKLM:\\SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall'
    $target = '${escapedName}'
    $items = Get-ChildItem -Path $base -ErrorAction SilentlyContinue
    $hit = $null
    foreach ($item in $items) {
      $p = Get-ItemProperty -Path $item.PSPath -ErrorAction SilentlyContinue
      if ($null -eq $p) { continue }
      if ($p.DisplayName -eq $target -or ($p.DisplayName -like "*$target*")) {
        $hit = [pscustomobject]@{
          RegistryKey = $item.Name
          DisplayName = [string]$p.DisplayName
          InstallSource = [string]$p.InstallSource
          InstallPath = [string]$p.InstallPath
        }
        break
      }
    }
    $hit | ConvertTo-Json -Compress
  `

  return runPowerShellJson(script)
}

function findExeInDir(rootDir, exeName, maxDepth = 4) {
  if (!rootDir || !fs.existsSync(rootDir)) return ''
  const stack = [{ dir: rootDir, depth: 0 }]

  while (stack.length > 0) {
    const current = stack.pop()
    if (!current) continue

    const { dir, depth } = current
    let entries = []
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true })
    } catch {
      continue
    }

    for (const entry of entries) {
      const full = path.join(dir, entry.name)
      if (entry.isFile() && entry.name.toLowerCase() === exeName.toLowerCase()) {
        return full
      }
      if (entry.isDirectory() && depth < maxDepth) {
        stack.push({ dir: full, depth: depth + 1 })
      }
    }
  }

  return ''
}

ipcMain.handle('game:auto-detect', (_event, gameId) => {
  const logs = []
  const meta = registryDetectMap[gameId]

  if (!meta) {
    return { ok: false, path: '', error: 'unsupported-game', logs: ['当前游戏未配置自动检测。'] }
  }

  logs.push(`目标: ${meta.displayName}`)
  logs.push(`读取字段: ${meta.valueName}`)
  logs.push(`目标EXE: ${meta.exeName}`)

  const entryRes = findUninstallEntry(meta.displayName)
  if (!entryRes.ok) {
    return {
      ok: false,
      path: '',
      error: 'registry-read-failed',
      logs: [...logs, `读取注册表失败: ${entryRes.error}`]
    }
  }

  const entry = entryRes.value
  if (!entry) {
    return {
      ok: false,
      path: '',
      error: 'registry-key-not-found',
      logs: [...logs, '未找到匹配 DisplayName 的卸载键。']
    }
  }

  logs.push(`命中卸载键: ${entry.RegistryKey}`)

  const installDir = String(entry[meta.valueName] || '').trim()
  if (!installDir) {
    return {
      ok: false,
      path: '',
      error: 'install-dir-empty',
      logs: [...logs, `未读取到 ${meta.valueName}。`]
    }
  }

  logs.push(`安装目录: ${installDir}`)

  if (!fs.existsSync(installDir)) {
    return {
      ok: false,
      path: '',
      error: 'install-dir-not-exists',
      logs: [...logs, '安装目录不存在或不可访问。']
    }
  }

  const exePath = findExeInDir(installDir, meta.exeName, 4)
  if (!exePath) {
    return {
      ok: false,
      path: '',
      error: 'exe-not-found',
      logs: [...logs, '目录内未找到目标EXE（已递归4层）。']
    }
  }

  logs.push(`命中EXE: ${exePath}`)
  return { ok: true, path: exePath, error: '', logs }
})

ipcMain.on('window:minimize', (event) => {
  const win = BrowserWindow.fromWebContents(event.sender)
  if (win) win.minimize()
})

ipcMain.on('window:close', (event) => {
  const win = BrowserWindow.fromWebContents(event.sender)
  if (win) win.close()
})

app.whenReady().then(() => {
  createWindow()
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})
