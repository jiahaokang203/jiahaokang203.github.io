from __future__ import annotations

import re
import threading
import time
from dataclasses import dataclass
from typing import Callable


@dataclass
class Command:
    raw: str
    game_name: str


class WeChatListener(threading.Thread):
    def __init__(
        self,
        target_chat: str,
        on_command: Callable[[Command], None],
        log: Callable[[str], None],
        poll_interval: float = 1.5,
    ) -> None:
        super().__init__(daemon=True)
        self.target_chat = target_chat
        self.on_command = on_command
        self.log = log
        self.poll_interval = poll_interval
        self._stop = threading.Event()
        self._seen: set[str] = set()

    def stop(self) -> None:
        self._stop.set()

    def run(self) -> None:
        try:
            from wxauto import WeChat
        except Exception as exc:
            self.log(f"wxauto 不可用，无法监听微信: {exc}")
            return

        try:
            wx = WeChat()
            wx.AddListenChat(who=self.target_chat, savepic=False)
            self.log(f"已开始监听微信会话: {self.target_chat}")
        except Exception as exc:
            self.log(f"监听初始化失败，请确认已登录 PC 微信并打开会话: {exc}")
            return

        while not self._stop.is_set():
            try:
                listen_data = wx.GetListenMessage()
                for text in self._extract_texts(listen_data):
                    key = f"{int(time.time() // 2)}::{text}"
                    if key in self._seen:
                        continue
                    self._seen.add(key)
                    cmd = self._parse(text)
                    if cmd:
                        self.log(f"收到指令: {cmd.raw}")
                        self.on_command(cmd)
            except Exception as exc:
                self.log(f"监听异常: {exc}")

            time.sleep(self.poll_interval)

    def _extract_texts(self, listen_data: object) -> list[str]:
        texts: list[str] = []

        if isinstance(listen_data, dict):
            values = listen_data.values()
        else:
            values = [listen_data]

        for item in values:
            if isinstance(item, list):
                messages = item
            else:
                messages = [item]

            for msg in messages:
                content = self._extract_single_text(msg)
                if content:
                    texts.append(content)

        return texts

    @staticmethod
    def _extract_single_text(msg: object) -> str:
        if msg is None:
            return ""

        for attr in ("content", "text", "msg", "message"):
            if hasattr(msg, attr):
                value = getattr(msg, attr)
                if isinstance(value, str):
                    return value.strip()

        if isinstance(msg, str):
            return msg.strip()

        return str(msg).strip()

    @staticmethod
    def _parse(text: str) -> Command | None:
        m = re.search(r"启动\s*[:：]?\s*(.+)", text)
        if not m:
            return None

        game_name = m.group(1).strip()
        if not game_name:
            return None

        return Command(raw=text, game_name=game_name)
