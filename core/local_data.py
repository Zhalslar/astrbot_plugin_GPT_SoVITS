from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from astrbot.api import logger

from .config import PluginConfig


class LocalDataManager:
    def __init__(self, config: PluginConfig):
        self.cfg = config.cache
        self.expire_seconds = self.cfg.expire_hours * 3600
        self.audio_dir: Path = config.audio_dir

    def _cache_path(self, params: dict[str, Any]) -> Path:
        """
        根据参数生成唯一音频文件路径
        """

        # 参数标准化
        payload = json.dumps(
            params,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        )

        # 计算 hash
        cache_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

        # 解析扩展名
        ext = str(params.get("media_type", "wav")).lower()
        if ext not in {"wav", "mp3", "ogg"}:
            ext = "wav"

        filename = f"gsv_{cache_hash}.{ext}"

        return (self.audio_dir / filename).resolve()

    def _is_expired(self, file_path: Path) -> bool:
        if self.expire_seconds == 0:
            return False

        age = datetime.now().timestamp() - file_path.stat().st_mtime
        return age > self.expire_seconds

    def get_cached_audio(self, params: dict[str, Any]) -> tuple[Path, bytes] | None:
        """
        尝试从缓存中读取音频文件
        """
        if not self.cfg.enabled:
            return None

        try:
            path = self._cache_path(params)

            if not path.exists():
                return None

            if self._is_expired(path):
                path.unlink(missing_ok=True)
                logger.debug(f"缓存已过期并删除: {path}")
                return None

            data = path.read_bytes()
            if not data:
                path.unlink(missing_ok=True)
                return None

            logger.debug(f"命中语音缓存: {path}")
            return path, data

        except Exception as e:
            logger.warning(f"读取缓存失败: {e}")
            return None

    def save_audio(
        self,
        data: bytes | None,
        params: dict[str, Any],
        overwrite: bool = True,
    ) -> Path | None:
        """
        保存音频文件 (仅启用缓存时生效)

        overwrite:
            True  -> 覆盖已存在文件
            False -> 若文件已存在则直接返回，不覆盖
        """
        if not self.cfg.enabled:
            return None

        if not data:
            logger.error("保存音频失败: 无音频数据")
            return None

        try:
            path = self._cache_path(params)

            if path.exists():
                if not overwrite:
                    logger.debug(f"文件已存在，跳过覆盖: {path}")
                    return path

            path.write_bytes(data)

            logger.info(f"已保存音频文件: {path}")
            return path

        except Exception as e:
            logger.error(f"保存音频失败: {e}")
            return None
