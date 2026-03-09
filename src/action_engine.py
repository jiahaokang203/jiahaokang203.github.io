from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Callable

import cv2
import numpy as np
import pyautogui

from .models import GameConfig


class ActionEngine:
    def __init__(self, log: Callable[[str], None]) -> None:
        self.log = log

    def launch(self, game: GameConfig) -> None:
        if not game.has_location:
            raise FileNotFoundError(f"未定位游戏: {game.name}")

        exe = Path(game.exe_path)
        self.log(f"启动游戏进程: {exe}")
        subprocess.Popen([str(exe)], cwd=str(exe.parent))

        if not game.actions:
            self.log("未配置自动化动作，已仅完成启动。")
            return

        self.log(f"开始执行动作，总数: {len(game.actions)}")
        for idx, action in enumerate(game.actions, start=1):
            action_type = str(action.get("type", "")).strip().lower()
            self.log(f"[{idx}/{len(game.actions)}] 执行动作: {action_type}")
            self._run_action(action_type, action)

        self.log("动作执行完成。")

    def _run_action(self, action_type: str, action: dict) -> None:
        if action_type == "wait":
            seconds = float(action.get("seconds", 1))
            time.sleep(seconds)
            return

        if action_type == "key":
            pyautogui.press(str(action.get("key", "enter")))
            return

        if action_type == "hotkey":
            keys = action.get("keys", [])
            if not isinstance(keys, list) or not keys:
                raise ValueError("hotkey 动作需要 keys 数组")
            pyautogui.hotkey(*[str(k) for k in keys])
            return

        if action_type == "click":
            x = int(action.get("x"))
            y = int(action.get("y"))
            pyautogui.click(x=x, y=y)
            return

        if action_type == "image_click":
            self._image_click(action)
            return

        raise ValueError(f"不支持的动作类型: {action_type}")

    def _image_click(self, action: dict) -> None:
        template_path = Path(str(action.get("template", "")).strip())
        if not template_path.exists():
            raise FileNotFoundError(f"模板图不存在: {template_path}")

        confidence = float(action.get("confidence", 0.85))
        timeout = float(action.get("timeout", 10))
        interval = float(action.get("interval", 0.5))
        offset_x = int(action.get("offset_x", 0))
        offset_y = int(action.get("offset_y", 0))

        template = cv2.imread(str(template_path), cv2.IMREAD_COLOR)
        if template is None:
            raise ValueError(f"无法读取模板图: {template_path}")

        t_height, t_width = template.shape[:2]
        start = time.time()

        while time.time() - start <= timeout:
            screenshot = pyautogui.screenshot()
            screen = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            res = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)

            if max_val >= confidence:
                cx = max_loc[0] + t_width // 2 + offset_x
                cy = max_loc[1] + t_height // 2 + offset_y
                pyautogui.click(x=cx, y=cy)
                self.log(f"image_click 命中，置信度: {max_val:.3f}，点击: ({cx}, {cy})")
                return

            time.sleep(interval)

        raise TimeoutError(f"image_click 超时，{timeout}s 内未识别到目标")
