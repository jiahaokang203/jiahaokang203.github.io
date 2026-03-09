from __future__ import annotations

import json
import shutil
from pathlib import Path

from .models import GameConfig


class ConfigStore:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.config_dir = self.base_dir / "config"
        self.default_file = self.config_dir / "default_games.json"
        self.user_file = self.config_dir / "games.json"

    def ensure(self) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        if not self.user_file.exists():
            shutil.copyfile(self.default_file, self.user_file)

    def load_games(self) -> list[GameConfig]:
        self.ensure()
        data = self._read_json(self.user_file)
        games = data.get("games", [])
        return [GameConfig.from_dict(item) for item in games]

    def save_games(self, games: list[GameConfig]) -> None:
        payload = {"games": [g.to_dict() for g in games]}
        self.user_file.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def import_action_config(self, game: GameConfig, config_file: Path) -> GameConfig:
        data = self._read_json(config_file)
        actions = data.get("actions")
        if not isinstance(actions, list):
            raise ValueError("配置文件必须包含 actions 数组")

        game.actions = actions
        game.config_path = str(config_file)
        return game

    @staticmethod
    def _read_json(file_path: Path) -> dict:
        # Accept both UTF-8 and UTF-8 BOM JSON files.
        return json.loads(file_path.read_text(encoding="utf-8-sig"))
