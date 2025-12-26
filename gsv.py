import re
from pathlib import Path
from typing import NamedTuple

from aiohttp import ClientError, ClientSession, ClientTimeout

from astrbot.api import logger
from astrbot.core import AstrBotConfig


class RequestResult(NamedTuple):
    ok: bool
    data: bytes | None = None
    error: str | None = None


class GPTSoVITSCore:
    def __init__(self, config: AstrBotConfig, data_dir: Path):
        self.conf = config
        self.data_dir = data_dir

        self.base_url: str = config["base_url"]

        self.gpt_weights_path = config["model"]["gpt_weights_path"]
        self.sovits_weights_path = config["model"]["sovits_weights_path"]

        self.default_params: dict = config["default_params"]
        self.default_emotion: str = config["default_emotion"]
        self.emotions: dict = config["emotions"]

        self.session: ClientSession | None = None

    # =====================
    # 生命周期
    # =====================

    async def initialize(self):
        self.session = ClientSession(timeout=ClientTimeout(total=30))

        if self.gpt_weights_path:
            await self._set_gpt_weights(str(Path(self.gpt_weights_path).resolve()))

        if self.sovits_weights_path:
            await self._set_sovits_weights(
                str(Path(self.sovits_weights_path).resolve())
            )

    async def terminate(self):
        if self.session:
            await self.session.close()

    # =====================
    # 基础工具
    # =====================

    def _generate_file_name(self, params: dict) -> str:
        sanitized = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff\s]", "", params["text"])
        name = sanitized.strip()[:30]
        return f"{name}.{self.default_params['media_type']}"

    def find_emotion(self, text: str) -> str | None:
        for emotion, params in self.emotions.items():
            for word in params.get("keywords", []):
                if word in text:
                    return emotion
        return None

    # =====================
    # 核心请求层（唯一入口）
    # =====================

    async def _request(
        self,
        endpoint: str,
        params: dict | None = None,
    ) -> RequestResult:
        if not self.session:
            return RequestResult(False, error="HTTP session not initialized")

        if params:
            params = {
                k: str(v).lower() if isinstance(v, bool) else v
                for k, v in params.items()
            }

        try:
            async with self.session.get(endpoint, params=params) as resp:
                if resp.status != 200:
                    return RequestResult(ok=False, error=f"HTTP {resp.status}")

                return RequestResult(ok=True, data=await resp.read())

        except ClientError as e:
            logger.error(f"[HTTP] 请求失败: {endpoint} | {e}")
            return RequestResult(False, error=str(e))

        except Exception as e:
            logger.exception(f"[HTTP] 未知异常: {endpoint}")
            return RequestResult(False, error=str(e))

    # =====================
    # 业务接口
    # =====================

    async def _set_gpt_weights(self, path: str):
        result = await self._request(
            f"{self.base_url}/set_gpt_weights",
            {"weights_path": path},
        )

        if result.ok:
            logger.info(f"GPT 模型已加载: {path}")
        else:
            logger.error(f"GPT 模型加载失败: {result.error}")

    async def _set_sovits_weights(self, path: str):
        result = await self._request(
            f"{self.base_url}/set_sovits_weights",
            {"weights_path": path},
        )

        if result.ok:
            logger.info(f"SoVITS 模型已加载: {path}")
        else:
            logger.error(f"SoVITS 模型加载失败: {result.error}")

    async def inference(self, text: str, emotion: str | None = None) -> str | None:
        params = self.default_params.copy()

        if emotion is None:
            emotion = self.find_emotion(text)

        if emotion:
            cfg = self.emotions.get(emotion, {}).copy()
            cfg.pop("keywords", None)
            params.update(cfg)
        if text:
            params["text"] = text

        result = await self._request(
            f"{self.base_url}/tts",
            params,
        )

        if not result.ok or not result.data:
            logger.warning(f"TTS 失败: {result.error}")
            return None

        save_path = self.data_dir / self._generate_file_name(params)
        save_path.write_bytes(result.data)

        return str(save_path)

    async def restart(self):
        result = await self._request(
            f"{self.base_url}/control",
            {"command": "restart"},
        )

        if not result.ok:
            logger.error(f"重启失败: {result.error}")
