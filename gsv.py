import re
from dataclasses import dataclass
from pathlib import Path

from aiohttp import ClientError, ClientSession, ClientTimeout

from astrbot.api import logger
from astrbot.core import AstrBotConfig


@dataclass
class GSVRequestResult:
    ok: bool
    data: bytes | None = None
    error: str | None = None


class GPTSoVITSCore:
    def __init__(self, config: AstrBotConfig):
        self.conf = config

        self.base_url: str = config["base_url"]

        self.gpt_weights_path = config["model"]["gpt_weights_path"]
        self.sovits_weights_path = config["model"]["sovits_weights_path"]

        self.default_params: dict = config["default_params"]
        self.emotions: dict = config["emotions"]

        self.session: ClientSession | None = None

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

    async def _request(
        self,
        endpoint: str,
        params: dict | None = None,
    ) -> GSVRequestResult:
        if not self.session:
            return GSVRequestResult(False, error="HTTP session not initialized")

        if params:
            params = {
                k: str(v).lower() if isinstance(v, bool) else v
                for k, v in params.items()
            }

        try:
            async with self.session.get(endpoint, params=params) as resp:
                if resp.status != 200:
                    detail = await resp.text()
                    return GSVRequestResult(
                        ok=False, error=f"HTTP {resp.status}: {detail}"
                    )

                return GSVRequestResult(ok=True, data=await resp.read())

        except ClientError as e:
            logger.error(f"[HTTP] 请求失败: {endpoint} | {e}")
            return GSVRequestResult(False, error=str(e))

        except Exception as e:
            logger.exception(f"[HTTP] 未知异常: {endpoint}")
            return GSVRequestResult(False, error=str(e))

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

    async def inference(self, text: str, emotion: str | None = None) -> GSVRequestResult:
        """
        TTS 推理
        :param text: 文本
        :param emotion: 情绪
        :return: 合成音频文件的路径
        """
        params = self.default_params.copy()

        if text:
            params["text"] = text

        if emotion is None:
            emotion = self.find_emotion(text)
            logger.debug(f"已匹配到情绪: {emotion}")

        if emotion:
            cfg = self.emotions.get(emotion, {}).copy()
            cfg.pop("keywords", None)
            params.update(cfg)

        if "ref_audio_path" in params:
            params["ref_audio_path"] = str(Path(params["ref_audio_path"]).resolve())

        logger.debug(f"向 GSV 发起请求，参数: {params}")

        result = await self._request(
            f"{self.base_url}/tts",
            params,
        )

        if not result.ok or not result.data:
            logger.error(f"TTS 失败: {result.error}")

        return result

    async def restart(self):
        """重启 GPT=-SoVITS"""
        result = await self._request(
            f"{self.base_url}/control",
            {"command": "restart"},
        )

        if not result.ok:
            logger.error(f"重启失败: {result.error}")
