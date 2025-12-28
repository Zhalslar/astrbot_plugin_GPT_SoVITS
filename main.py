import random

from astrbot.api import logger
from astrbot.api.event import filter
from astrbot.api.star import Context, Star
from astrbot.core import AstrBotConfig
from astrbot.core.message.components import Plain, Record
from astrbot.core.platform import AstrMessageEvent
from astrbot.core.star.star_tools import StarTools

from .gsv import GPTSoVITSCore


class GPTSoVITSPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.conf = config
        self.data_dir = StarTools.get_data_dir("astrbot_plugin_GPT_SoVITS")

        self.only_llm_result: bool = self.conf["auto"]["only_llm_result"]
        self.tts_prob: float = self.conf["auto"]["tts_prob"]
        self.max_llm_len: int = self.conf["auto"]["max_llm_len"]

        self.enabled = config["enabled"]
        self.gsv: GPTSoVITSCore | None = None

    async def initialize(self):
        if not self.enabled:
            return
        try:
            self.gsv = GPTSoVITSCore(self.conf, self.data_dir)
            await self.gsv.initialize()
        except Exception as e:
            logger.error(
                f"GPT-SoVITS 核心初始化失败，插件已自动关闭业务功能, 报错：{e}"
            )
            self.enabled = False
            self.conf.save_config()

    async def terminate(self):
        if self.gsv:
            await self.gsv.terminate()

    @filter.on_decorating_result()
    async def on_decorating_result(self, event: AstrMessageEvent):
        """消息入口"""
        result = event.get_result()
        if not result:
            return
        chain = result.chain
        if not chain:
            return

        if self.only_llm_result and not result.is_llm_result():
            return

        if random.random() > self.tts_prob:
            return

        # 仅允许只含有单条文本的消息链通过
        seg = chain[0]
        if not (len(chain) == 1 and isinstance(seg, Plain)):
            return

        # 仅允许一定长度以下的文本通过
        if len(seg.text) > self.max_llm_len:
            return

        if not self.gsv:
            return

        result = await self.gsv.inference(seg.text)
        if result.path:
            chain.clear()
            chain.append(Record.fromFileSystem(result.path))

    @filter.command("说", alias={"gsv", "GSV"})
    async def on_command(self, event: AstrMessageEvent):
        """说 <内容>, 直接调用GSV合成语音"""
        if not self.gsv:
            return
        text = event.message_str.partition(" ")[2]
        result = await self.gsv.inference(text)
        seg = (
            Record.fromFileSystem(result.path)
            if result.path
            else Plain(str(result.error))
        )
        yield event.chain_result([seg])

    @filter.command("重启GSV", alias={"重启gsv"})
    async def tts_control(self, event: AstrMessageEvent):
        """重启GPT_SoVITS"""
        if not self.gsv:
            return
        yield event.plain_result("重启TTS中...(报错信息请忽略，等待一会即可完成重启)")
        await self.gsv.restart()
