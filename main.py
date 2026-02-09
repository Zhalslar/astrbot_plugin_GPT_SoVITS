import random

from astrbot.api.event import filter
from astrbot.api.star import Context, Star
from astrbot.core import AstrBotConfig
from astrbot.core.message.components import Plain, Record
from astrbot.core.platform import AstrMessageEvent

from .core.client import GSVApiClient
from .core.service import GPTSoVITSService
from .core.config import PluginConfig
from .core.entry import EntryManager
from .core.emotion import EmotionJudger


class GPTSoVITSPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.cfg = PluginConfig(config, context)
        self.entry_mgr = EntryManager(self.cfg)
        self.client = GSVApiClient(self.cfg)
        self.judger = EmotionJudger(self.cfg)
        self.service = GPTSoVITSService(self.cfg, self.client)

    async def initialize(self):
        if self.cfg.enabled:
            await self.service.load_model()

    async def terminate(self):
        await self.client.close()

    async def _get_emotion_params(
        self,
        text: str,
        event: AstrMessageEvent | None = None,
    ) -> dict | None:
        entry = None

        if self.cfg.judge.enabled_llm and event:
            labels = self.entry_mgr.get_names()
            emotion = await self.judger.judge_emotion(
                event,
                text=text,
                labels=labels,
            )
            if emotion:
                entry = self.entry_mgr.get_entry(emotion)

        if entry is None:
            entry = self.entry_mgr.match_entry(text)

        return entry.to_params() if entry else None

    @filter.on_decorating_result(priority=14)
    async def on_decorating_result(self, event: AstrMessageEvent):
        """消息入口"""
        if not self.cfg.enabled:
            return
        cfg = self.cfg.auto

        result = event.get_result()
        if not result:
            return
        chain = result.chain
        if not chain:
            return
        if cfg.only_llm_result and not result.is_llm_result():
            return
        if random.random() > cfg.tts_prob:
            return

        # 收集所有Plain文本片段
        plain_texts = []
        for seg in chain:
            if isinstance(seg, Plain):
                plain_texts.append(seg.text)

        # 仅允许只含有Plain的消息链通过
        if len(plain_texts) != len(chain):
            return

        # 合并所有Plain文本
        combined_text = "\n".join(plain_texts)

        # 仅允许一定长度以下的文本通过
        if len(combined_text) > cfg.max_msg_len:
            return

        params = await self._get_emotion_params(combined_text, event)
        result = await self.service.inference(combined_text, extra_params=params)
        if result.ok:
            chain.clear()
            chain.append(Record.fromBase64(result.to_bs64()))

    @filter.command("说", alias={"gsv", "GSV"})
    async def on_command(self, event: AstrMessageEvent):
        """说 <内容>, 直接调用GSV合成语音"""
        if not self.cfg.enabled:
            return
        text = event.message_str.partition(" ")[2]
        result = await self.service.inference(text)
        seg = Record.fromBase64(result.to_bs64()) if result.ok else Plain(result.error)
        yield event.chain_result([seg])

    @filter.command("重启GSV", alias={"重启gsv"})
    async def tts_control(self, event: AstrMessageEvent):
        """重启GPT_SoVITS"""
        if not self.cfg.enabled:
            return
        yield event.plain_result("重启TTS中...(报错信息请忽略，等待一会即可完成重启)")
        await self.service.restart()

    @filter.llm_tool()
    async def gsv_tts(self, event: AstrMessageEvent, message: str = ""):
        """
        用语音输出要讲的话
        Args:
            message(string): 要讲的话
            get_image(boolean): 是否获取当前对话中的图片附加到说说里, 默认为True
        """
        try:
            params = await self._get_emotion_params(message, event)
            result = await self.service.inference(message, extra_params=params)
            if result.ok:
                seg = Record.fromBase64(result.to_bs64())
                await event.send(event.chain_result([seg]))
            else:
                return result.error
        except Exception as e:
            return str(e)
