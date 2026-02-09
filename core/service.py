from typing import Any
from astrbot.api import logger

from .config import PluginConfig
from .client import GSVApiClient, GSVRequestResult


class GPTSoVITSService:
    def __init__(
        self,
        config: PluginConfig,
        client: GSVApiClient,
    ):
        self.cfg = config.model
        self.default_params = config.default_params
        self.client = client

    async def load_model(self):
        if self.cfg.gpt_path:
            result = await self.client.set_gpt_weights(self.cfg.gpt_path)
            if result.ok:
                logger.info(f"GPT 模型已加载: {self.cfg.gpt_path}")
            else:
                logger.error(f"GPT 模型加载失败: {result.error}")

        if self.cfg.sovits_path:
            result = await self.client.set_sovits_weights(self.cfg.sovits_path)
            if result.ok:
                logger.info(f"SoVITS 模型已加载: {self.cfg.sovits_path}")
            else:
                logger.error(f"SoVITS 模型加载失败: {result.error}")

    async def inference(
        self,
        text: str,
        extra_params: dict[str, Any] | None = None,
    ) -> GSVRequestResult:
        """TTS 推理"""
        params = self.default_params.copy()
        if text:
            params["text"] = text

        if extra_params:
            filtered_params = {
                k: v for k, v in extra_params.items() if k in params
            }
            params.update(filtered_params)
            logger.debug(f"已更新已有参数: {filtered_params}")


        logger.debug(f"向 GSV 发起 TTS 请求，参数: {params}")
        result = await self.client.tts(params)

        if not result.ok or not result.data:
            logger.error(f"TTS 失败: {result.error}")

        return result

    async def restart(self):
        result = await self.client.restart()
        if not result.ok:
            logger.error(f"重启失败: {result.error}")
