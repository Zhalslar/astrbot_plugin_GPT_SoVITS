from dataclasses import dataclass

from aiohttp import ClientError, ClientSession, ClientTimeout

from astrbot.api import logger

from .config import PluginConfig


@dataclass
class GSVRequestResult:
    ok: bool
    data: bytes | None = None
    error: str = ""
    text: str = ""
    file_path: str = ""

    @property
    def size(self) -> int:
        """音频数据大小（字节）"""
        return len(self.data) if self.data else 0

    @property
    def is_empty(self) -> bool:
        """是否无数据"""
        return self.size == 0

    def __bool__(self) -> bool:
        return self.ok and not self.is_empty



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
        request_text = ""
        if params:
            request_text = str(params.get("text", ""))
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
                        text=request_text,
                    )

                return GSVRequestResult(
                    ok=True,
                    data=await resp.read(),
                    text=request_text,
                )

        except ClientError as e:
            logger.error(f"[HTTP] 请求失败: {url} | {e}")
            return GSVRequestResult(False, error=str(e), text=request_text)

        except Exception as e:
            logger.exception(f"[HTTP] 未知异常: {url}")
            return GSVRequestResult(False, error=str(e), text=request_text)

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
