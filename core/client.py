import base64
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from aiohttp import ClientError, ClientSession, ClientTimeout

from astrbot.api import logger

from .config import PluginConfig


@dataclass
class GSVRequestResult:
    ok: bool
    data: bytes | None = None
    error: str = ""

    def __bool__(self) -> bool:
        return self.ok and self.data is not None

    def to_bs64(self) -> str:
        if self.data is None:
            return ""
        return base64.urlsafe_b64encode(self.data).decode()

    def save(self, path: str | Path, filename: str | None = None) -> Path:
        """
        保存音频到指定路径

        Args:
            path: 目录路径或完整文件路径
            filename: 文件名（如果 path 是目录则必填）

        Returns:
            保存后的完整路径
        """
        if self.data is None:
            raise ValueError("无音频数据可保存")

        target = Path(path)

        # 如果 path 是目录，需要 filename
        if target.is_dir() or (not target.suffix and filename):
            if not filename:
                # 自动生成时间戳文件名
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"gsv_{timestamp}.wav"
            target = target / filename

        # 确保父目录存在
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(self.data)

        return target.resolve()

    @property
    def size(self) -> int:
        """音频数据大小（字节）"""
        return len(self.data) if self.data else 0

    @property
    def is_empty(self) -> bool:
        """是否无数据"""
        return self.data is None or len(self.data) == 0


class GSVApiClient:
    """
    API 层（HTTP 通信）
    """

    def __init__(self, config: PluginConfig):
        self.cfg = config.client
        self.base_url = self.cfg.base_url.rstrip("/")
        self.gpt_url = f"{self.base_url}/set_gpt_weights"
        self.sovits_url = f"{self.base_url}/set_sovits_weights"
        self.control_url = f"{self.base_url}/control"
        self.tts_url = f"{self.base_url}/tts"

        self.session = ClientSession(timeout=ClientTimeout(total=self.cfg.timeout))

    async def close(self):
        if self.session:
            await self.session.close()

    async def _request(
        self,
        url: str,
        *,
        params: dict | None = None,
    ) -> GSVRequestResult:
        if params:
            params = {
                k: str(v).lower() if isinstance(v, bool) else v
                for k, v in params.items()
            }

        try:
            async with self.session.get(url, params=params) as resp:
                if resp.status != 200:
                    detail = await resp.text()
                    return GSVRequestResult(
                        ok=False,
                        error=f"HTTP {resp.status}: {detail}",
                    )

                return GSVRequestResult(
                    ok=True,
                    data=await resp.read(),
                )

        except ClientError as e:
            logger.error(f"[HTTP] 请求失败: {url} | {e}")
            return GSVRequestResult(False, error=str(e))

        except Exception as e:
            logger.exception(f"[HTTP] 未知异常: {url}")
            return GSVRequestResult(False, error=str(e))

    async def set_gpt_weights(self, path: str) -> GSVRequestResult:
        return await self._request(
            self.gpt_url,
            params={"weights_path": path},
        )

    async def set_sovits_weights(self, path: str) -> GSVRequestResult:
        return await self._request(
            self.sovits_url,
            params={"weights_path": path},
        )

    async def tts(self, params: dict) -> GSVRequestResult:
        return await self._request(
            self.tts_url,
            params=params,
        )

    async def restart(self) -> GSVRequestResult:
        return await self._request(
            self.control_url,
            params={"command": "restart"},
        )
