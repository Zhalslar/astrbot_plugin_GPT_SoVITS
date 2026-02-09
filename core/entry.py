# config.py
from __future__ import annotations
from pathlib import Path
from typing import Any

import yaml
from astrbot.api import logger
from .config import PluginConfig, ConfigNode


class EmotionEntry(ConfigNode):
    name: str
    keywords: list[str]
    ref_audio_path: str
    prompt_text: str
    prompt_lang: str
    speed_factor: float
    fragment_interval: float

    def __init__(self, data: dict[str, Any]):
        super().__init__(data)
        self.ref_audio_path = PluginConfig.normalize_path(self.ref_audio_path)

    def to_params(self) -> dict[str, Any]:
        return {
            "ref_audio_path": self.ref_audio_path,
            "prompt_text": self.prompt_text,
            "prompt_lang": self.prompt_lang,
            "speed_factor": self.speed_factor,
            "fragment_interval": self.fragment_interval,
        }


class EntryManager:
    def __init__(self, config: PluginConfig):
        self.cfg = config
        self.entries: list[EmotionEntry] = [
            EmotionEntry(item) for item in self.cfg.entry_storage
        ]
        self.load_builtin_entry()
        logger.debug(f"已注册情绪：{[e.name for e in self.entries]}")

    def load_builtin_entry(self) -> None:
        file = self.cfg.builtin_entry_file
        try:
            with file.open("r", encoding="utf-8") as f:
                data: list[dict[str, Any]] = yaml.safe_load(f) or []
                self.add_entry(data)
        except Exception as e:
            logger.error(e)

    def add_entry(self, data: list[dict[str, Any]], key="name") -> None:
        existed = {e.name for e in self.entries}
        new_items: list[dict[str, Any]] = []

        for item in data:
            if key not in item or item[key] in existed:
                continue
            self.cfg.entry_storage.append(item)
            new_items.append(item)
            self.entries.append(EmotionEntry(item))

        if new_items:
            self.cfg.save_config()
            logger.info(f"已加载提示词：{[item[key] for item in new_items]}")

    def get_entry(self, name: str) -> EmotionEntry | None:
        """获取条目"""
        for entry in self.entries:
            if entry.name == name:
                return entry

    def match_entry(self, message: str) -> EmotionEntry | None:
        """匹配条目"""
        for entry in self.entries:
            for keyword in entry.keywords:
                if keyword in message:
                    return entry
