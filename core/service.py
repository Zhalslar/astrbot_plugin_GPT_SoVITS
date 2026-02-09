from astrbot.api import logger
from astrbot.core.platform.astr_message_event import AstrMessageEvent

from .config import PluginConfig
from .client import GSVApiClient, GSVRequestResult
from .entry import EntryManager, EmotionEntry
from .emotion import EmotionJudger


class GPTSoVITSService:
    def __init__(
        self,
        config: PluginConfig,
        client: GSVApiClient,
        entry_mgr: EntryManager,
        judger: EmotionJudger,
    ):
        self.cfg = config.model
        self.default_params = config.default_params
        self.client = client
        self.entry_mgr = entry_mgr
        self.judger = judger
        self.llm_judge_emotion = config.judge.enabled_llm

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

    async def _judge_entry(
        self,
        text: str,
        event: AstrMessageEvent | None = None,
    ) -> EmotionEntry | None:
        entry = None
        if self.llm_judge_emotion and event:
            labels = self.entry_mgr.get_names()
            emotion = await self.judger.judge_emotion(event, text=text, labels=labels)
            if emotion:
                entry = self.entry_mgr.get_entry(emotion)
        if not entry:
            entry = self.entry_mgr.match_entry(text)
        return entry


    async def inference(
        self,
        text: str,
        event: AstrMessageEvent | None = None,
    ) -> GSVRequestResult:
        """TTS 推理"""
        params = self.default_params.copy()

        if text:
            params["text"] = text

        if entry := await self._judge_entry(text, event):
            params.update(entry.to_params())
            logger.debug(f"已匹配到情绪: {entry.name}, 已添加到参数中")

        logger.debug(f"向 GSV 发起 TTS 请求，参数: {params}")
        result = await self.client.tts(params)

        if not result.ok or not result.data:
            logger.error(f"TTS 失败: {result.error}")

        return result

    async def restart(self):
        result = await self.client.restart()
        if not result.ok:
            logger.error(f"重启失败: {result.error}")
