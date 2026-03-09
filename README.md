# 游戏远程启动器（Windows）

## 功能
- 主界面选择游戏（支持 6 款游戏，底部卡片可左右滑动）
- 每个游戏独立配置
  - 定位游戏 exe（必填）
  - 导入动作配置 JSON（可选）
- 支持微信远程指令（基于 `wxauto`）
  - 指令格式：`启动游戏名`，例如：`启动原神`
- 动作引擎支持
  - `wait` 等待
  - `key` 单键
  - `hotkey` 组合键
  - `click` 坐标点击
  - `image_click` OpenCV 识别模板后点击

## 安装
```powershell
pip install -r requirements.txt
# 如需微信远程控制，再安装：
# pip install wxauto
```

## 运行
```powershell
python main.py
```

## 使用流程
1. 打开程序后，在主界面点击某个游戏卡片进入游戏页。
2. 点击“选择游戏exe”完成定位（必须）。
3. 如需自动化动作，点击“导入JSON配置”。
4. 点击“保存当前配置”。
5. 回到主界面，输入要监听的微信会话名称（默认“文件传输助手”），点击“启动微信监听”。
6. 在微信里发送：`启动原神`（或其他游戏名），程序会执行启动。

## 配置文件说明
- 默认游戏列表：`config/default_games.json`
- 用户保存配置：`config/games.json`（首次运行自动生成）
- 动作配置示例：`config/sample_actions.json`

示例：
```json
{
  "actions": [
    {"type": "wait", "seconds": 8},
    {"type": "key", "key": "enter"},
    {"type": "click", "x": 960, "y": 540},
    {
      "type": "image_click",
      "template": "C:/templates/start_btn.png",
      "confidence": 0.85,
      "timeout": 10,
      "interval": 0.5
    }
  ]
}
```

## 注意
- 如需微信远程控制，请额外安装 `wxauto` 并登录电脑版微信。
- 建议先用“本地测试启动”验证动作，再通过微信远程触发。
- `image_click` 依赖屏幕分辨率和 UI 状态，建议用当前分辨率截取模板图。

## 宣传页（GitHub Pages）
- 宣传页源码：`docs/`
- 入口文件：`docs/index.html`
- 已包含自动部署工作流：`.github/workflows/deploy-pages.yml`

发布方法：
1. 把仓库推送到 GitHub 的 `main` 分支。
2. 在仓库 `Settings -> Pages` 中将 `Build and deployment` 设为 `GitHub Actions`。
3. 推送后等待 Actions 执行完成，即可访问 Pages 地址。

