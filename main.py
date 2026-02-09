import base64
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

class GPTSoVITSPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.cfg = PluginConfig(config, context)
        self.entry_mgr = EntryManager(self.cfg)
        self.client = GSVApiClient(self.cfg)
        self.service = GPTSoVITSService(self.cfg, self.client, self.entry_mgr)


    async def initialize(self):
        if self.cfg.enabled:
            await self.service.load_model()

    async def terminate(self):
        await self.client.close()

    @filter.on_decorating_result()
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

        result = await self.service.inference(combined_text)
        if result.ok and result.data:
            chain.clear()
            b64_str = base64.urlsafe_b64encode(result.data).decode()
            chain.append(Record.fromBase64(b64_str))

    @filter.command("说", alias={"gsv", "GSV"})
    async def on_command(self, event: AstrMessageEvent):
        """说 <内容>, 直接调用GSV合成语音"""
        text = event.message_str.partition(" ")[2]
        result = await self.service.inference(text)
        seg = (
            Record.fromBase64(base64.urlsafe_b64encode(result.data).decode())
            if result.ok and result.data
            else Plain(str(result.error))
        )
        yield event.chain_result([seg])

    @filter.command("重启GSV", alias={"重启gsv"})
    async def tts_control(self, event: AstrMessageEvent):
        """重启GPT_SoVITS"""
        yield event.plain_result("重启TTS中...(报错信息请忽略，等待一会即可完成重启)")
        await self.service.restart()
