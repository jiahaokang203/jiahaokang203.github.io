import { useMemo, useRef, useState } from 'react'

const STORE_KEY = 'launcher_game_configs_v1'

const games = [
  { id: 'nz_future', name: '逆战:未来', subtitle: '射击 / 战术推进', image: '/images/nz_future.jpg', configImage: '/images/configbg/nz_future.png', cardImage: '/images/cards/nz_future_card.jpg', accent: '#d6ff24' },
  { id: 'delta_force', name: '三角洲行动', subtitle: '战术竞技 / 协同作战', image: '/images/delta_force.jpg', configImage: '/images/configbg/delta_force.png', cardImage: '/images/cards/delta_force_card.jpg', accent: '#4ec7ff' },
  { id: 'genshin', name: '原神', subtitle: '开放世界 / 冒险探索', image: '/images/genshin.jpg', configImage: '/images/configbg/genshin.png', cardImage: '/images/cards/genshin_card.jpg', accent: '#c3d8ff' },
  { id: 'wuthering_waves', name: '鸣潮', subtitle: '开放世界 / 动作 RPG', image: '/images/wuthering_waves.jpg', configImage: '/images/configbg/wuthering_waves.png', cardImage: '/images/cards/wuthering_waves_card.jpg', accent: '#ffd24a' },
  { id: 'hsr', name: '崩坏:星穹铁道', subtitle: '银河冒险 / 回合策略', image: '/images/hsr.png', configImage: '/images/configbg/hsr.png', cardImage: '/images/cards/hsr_card.jpg', accent: '#b0c5ff' },
  { id: 'snowbreak', name: '尘白禁区', subtitle: '轻科幻 / 3D 射击', image: '/images/snowbreak.png', configImage: '/images/configbg/snowbreak.png', cardImage: '/images/cards/snowbreak_card.jpg', accent: '#a8f3ff' }
]

const softwareCatalog = {
  nz_future: [
    {
      id: 'auto_assistant',
      name: 'Auto',
      intro: '基于视觉识别的塔防流程自动化软件,支持多种配置自定义,功能强大',
      shortcut: 'E:/desktop/assets/game/Auto.exe.lnk',
      icon: '/images/software/auto.ico'
    }
  ]
}

function loadConfigs() {
  try {
    const raw = localStorage.getItem(STORE_KEY)
    if (!raw) return {}
    return JSON.parse(raw)
  } catch {
    return {}
  }
}

function DesktopButtons({ onSettings }) {
  const api = window.launcherApi
  const isDesktop = Boolean(api && api.isDesktop)

  return (
    <div className="window-controls no-drag">
      <button type="button" className="win-btn" onClick={onSettings} title="设置">⚙</button>
      <button type="button" className="win-btn" onClick={() => isDesktop && api.minimize()} title="最小化">─</button>
      <button type="button" className="win-btn close" onClick={() => isDesktop && api.close()} title="关闭">×</button>
    </div>
  )
}

function MainView({ activeIndex, setActiveIndex, onOpenConfig }) {
  const rowRef = useRef(null)
  const activeGame = useMemo(() => games[activeIndex] ?? games[0], [activeIndex])

  const scrollCards = (delta) => {
    if (!rowRef.current) return
    rowRef.current.scrollBy({ left: delta, behavior: 'smooth' })
  }

  return (
    <>
      <div className="backgrounds">
        {games.map((game, index) => (
          <div
            key={game.id}
            className={`bg-layer ${index === activeIndex ? 'active' : ''}`}
            style={{ backgroundImage: `url(${game.image})` }}
          />
        ))}
      </div>

      <div className="overlay" />

      <section className="hero">
        <h1>{activeGame.name}</h1>
        <p>{activeGame.subtitle}</p>
      </section>

      <section className="cards-wrap">
        <button type="button" className="scroll-btn no-drag" aria-label="向左滚动" onClick={() => scrollCards(-340)}>‹</button>

        <div
          className="cards-row no-drag"
          ref={rowRef}
          onWheel={(e) => {
            if (Math.abs(e.deltaX) > Math.abs(e.deltaY)) return
            e.currentTarget.scrollBy({ left: e.deltaY, behavior: 'auto' })
          }}
        >
          {games.map((game, index) => {
            const isActive = index === activeIndex
            return (
              <button
                key={game.id}
                type="button"
                className={`game-card ${isActive ? 'active' : ''}`}
                style={{ '--accent': game.accent }}
                onMouseEnter={() => setActiveIndex(index)}
                onFocus={() => setActiveIndex(index)}
                onClick={() => onOpenConfig(game.id)}
              >
                <img src={game.cardImage} alt={game.name} loading="lazy" />
                <span className="game-name">{game.name}</span>
                <span className="card-frame" />
              </button>
            )
          })}
        </div>

        <button type="button" className="scroll-btn no-drag" aria-label="向右滚动" onClick={() => scrollCards(340)}>›</button>
      </section>
    </>
  )
}

function AddSoftwareModal({ gameId, onClose, onConfirm }) {
  const stageRef = useRef(null)
  const [hoveredId, setHoveredId] = useState('')
  const [pickedId, setPickedId] = useState('')
  const [tip, setTip] = useState(null)

  const softwareList = softwareCatalog[gameId] || []
  const picked = softwareList.find((x) => x.id === pickedId)

  const showTipFor = (item, target) => {
    const stage = stageRef.current?.getBoundingClientRect()
    const rect = target.getBoundingClientRect()
    if (!stage) return
    setTip({
      text: item.intro,
      left: rect.right - stage.left + 12,
      top: rect.top - stage.top
    })
  }

  return (
    <div className="modal-mask no-drag" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <h3>请选择添加的软件</h3>

        <div className="software-stage" ref={stageRef}>
          <div className="software-list">
            {softwareList.map((item) => (
              <button
                key={item.id}
                type="button"
                className={`software-item ${item.id === pickedId ? 'picked' : ''} ${item.id === hoveredId ? 'hovered' : ''}`}
                onMouseEnter={(e) => {
                  setHoveredId(item.id)
                  showTipFor(item, e.currentTarget)
                }}
                onFocus={(e) => {
                  setHoveredId(item.id)
                  showTipFor(item, e.currentTarget)
                }}
                onMouseLeave={() => {
                  setHoveredId('')
                  setTip(null)
                }}
                onBlur={() => {
                  setHoveredId('')
                  setTip(null)
                }}
                onClick={() => setPickedId((prev) => (prev === item.id ? '' : item.id))}
              >
                <span className="software-icon-wrap">
                  <img className="software-icon-img" src={item.icon} alt={item.name} />
                </span>
                <span className="software-name">{item.name}</span>
              </button>
            ))}
          </div>

          {tip ? (
            <div className="software-tip" style={{ left: `${tip.left}px`, top: `${tip.top}px` }}>
              <p className="software-intro">{tip.text}</p>
            </div>
          ) : null}
        </div>

        <div className="modal-actions">
          <button type="button" className="btn ghost" onClick={onClose}>取消</button>
          <button
            type="button"
            className="btn"
            disabled={!picked}
            onClick={() => {
              if (!picked) return
              const ok = window.confirm(`是否确认添加 ${picked.name} ?`)
              if (!ok) return
              onConfirm(picked)
            }}
          >
            确认添加
          </button>
        </div>
      </div>
    </div>
  )
}

function ConfigView({ game, config, onBack, onUpdate, onAutoDetect, onOpenAddConfig, closing }) {
  const exeInputRef = useRef(null)
  const [detecting, setDetecting] = useState(false)
  const addedSoftware = config.addedSoftware || []

  return (
    <>
      <div className={`config-bg ${closing ? 'scene-leave' : 'scene-enter'}`} style={{ backgroundImage: `url(${game.configImage})` }} />
      <div className={`config-overlay ${closing ? 'scene-leave' : ''}`} />

      <section className={`config-hero ${closing ? 'scene-down' : 'scene-up'}`}>
        <button type="button" className="back-btn no-drag" onClick={onBack}>← 返回主页</button>
        <h2>{game.name} 配置</h2>
      </section>

      <section className={`config-panel no-drag ${closing ? 'scene-down' : 'scene-up'}`}>
        <div className="field-block">
          <label>定位游戏（必填）</label>
          <div className="field-row locate-row">
            <input value={config.exePath || ''} readOnly placeholder="请选择游戏 exe" />
            <button type="button" onClick={() => exeInputRef.current?.click()}>手动定位</button>
            <button
              type="button"
              disabled={detecting}
              onClick={async () => {
                setDetecting(true)
                const result = await onAutoDetect(game.id)
                setDetecting(false)

                if (result.ok && result.path) {
                  onUpdate({ exePath: result.path })
                  window.alert(`自动检测成功:\n${result.path}`)
                } else {
                  const lines = (result.logs || []).join('\n')
                  window.alert(`自动检测失败（${result.error || 'unknown'}）:\n${lines}`)
                }
              }}
            >
              {detecting ? '检测中...' : '自动检测'}
            </button>
          </div>

          <input
            ref={exeInputRef}
            className="hidden-input"
            type="file"
            accept=".exe"
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (!file) return
              onUpdate({ exePath: file.name })
            }}
          />
        </div>

        <div className="field-block">
          <label>添加配置</label>
          <div className="field-row add-row">
            <input
              value={addedSoftware.length ? addedSoftware.map((x) => x.name).join('，') : ''}
              readOnly
              placeholder="尚未添加软件"
            />
            <button
              type="button"
              disabled={game.id !== 'nz_future'}
              onClick={onOpenAddConfig}
            >
              添加配置
            </button>
          </div>
        </div>

        <div className="status-line">状态：{config.exePath ? '已定位' : '未定位'}</div>
      </section>
    </>
  )
}

export default function App() {
  const [activeIndex, setActiveIndex] = useState(0)
  const [showSettings, setShowSettings] = useState(false)
  const [selectedGameId, setSelectedGameId] = useState(null)
  const [configs, setConfigs] = useState(loadConfigs)
  const [isClosingConfig, setIsClosingConfig] = useState(false)
  const [showAddModal, setShowAddModal] = useState(false)

  const selectedGame = useMemo(() => games.find((g) => g.id === selectedGameId) ?? null, [selectedGameId])

  const updateGameConfig = (gameId, patch) => {
    setConfigs((prev) => {
      const next = { ...prev, [gameId]: { ...(prev[gameId] || {}), ...patch } }
      localStorage.setItem(STORE_KEY, JSON.stringify(next))
      return next
    })
  }

  const autoDetectGame = async (gameId) => {
    const api = window.launcherApi
    if (!api || !api.autoDetectGame) {
      return {
        ok: false,
        path: '',
        error: 'not-desktop-mode',
        logs: ['当前不是桌面模式（Electron），无法读取本机注册表。请用桌面模式启动。']
      }
    }

    try {
      const result = await api.autoDetectGame(gameId)
      if (result && typeof result === 'object') return result
      if (typeof result === 'string' && result) {
        return { ok: true, path: result, error: '', logs: ['检测成功（兼容旧返回格式）。'] }
      }
      return { ok: false, path: '', error: 'unknown-empty', logs: ['未返回有效检测结果。'] }
    } catch (err) {
      return {
        ok: false,
        path: '',
        error: 'invoke-failed',
        logs: [String(err)]
      }
    }
  }

  const onBackToMain = () => {
    setIsClosingConfig(true)
    setTimeout(() => {
      setSelectedGameId(null)
      setIsClosingConfig(false)
      setShowAddModal(false)
    }, 240)
  }

  return (
    <div className="page">
      <header className="topbar app-drag">
        <div className="brand no-drag">
          <span className="dot" />
          <span>Game Hub</span>
        </div>
        <DesktopButtons onSettings={() => setShowSettings((v) => !v)} />
      </header>

      {showSettings && (
        <aside className="settings-panel no-drag">
          <h3>设置</h3>
          <p>这里预留后续功能：下载设置、启动参数、微信机器人配置。</p>
        </aside>
      )}

      {!selectedGame ? (
        <MainView activeIndex={activeIndex} setActiveIndex={setActiveIndex} onOpenConfig={setSelectedGameId} />
      ) : (
        <>
          <ConfigView
            game={selectedGame}
            config={configs[selectedGame.id] || {}}
            closing={isClosingConfig}
            onBack={onBackToMain}
            onAutoDetect={autoDetectGame}
            onOpenAddConfig={() => setShowAddModal(true)}
            onUpdate={(patch) => updateGameConfig(selectedGame.id, patch)}
          />

          {showAddModal && selectedGame.id === 'nz_future' && (
            <AddSoftwareModal
              gameId={selectedGame.id}
              onClose={() => setShowAddModal(false)}
              onConfirm={(software) => {
                const current = configs[selectedGame.id]?.addedSoftware || []
                const exists = current.some((x) => x.id === software.id)
                if (!exists) {
                  updateGameConfig(selectedGame.id, { addedSoftware: [...current, software] })
                }
                setShowAddModal(false)
                window.alert('添加成功。')
              }}
            />
          )}
        </>
      )}
    </div>
  )
}
