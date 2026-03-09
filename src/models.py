from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class GameConfig:
    id: str
    name: str
    exe_path: str = ""
    config_path: str = ""
    actions: list[dict[str, Any]] = field(default_factory=list)

    @property
    def has_location(self) -> bool:
        return bool(self.exe_path and Path(self.exe_path).exists())

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "GameConfig":
        return cls(
            id=str(payload.get("id", "")).strip(),
            name=str(payload.get("name", "")).strip(),
            exe_path=str(payload.get("exe_path", "")).strip(),
            config_path=str(payload.get("config_path", "")).strip(),
            actions=list(payload.get("actions", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "exe_path": self.exe_path,
            "config_path": self.config_path,
            "actions": self.actions,
        }
