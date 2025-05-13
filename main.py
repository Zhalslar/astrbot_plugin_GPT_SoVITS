import asyncio
import re
import random
import aiohttp
from astrbot import logger
from astrbot.api.event import filter
from astrbot.api.star import Context, Star, register
from astrbot.core import AstrBotConfig
from astrbot.core.message.components import Record
from astrbot.core.platform import AstrMessageEvent
import astrbot.core.message.components as Comp
from pathlib import Path
from typing import Dict


SAVED_AUDIO_DIR = Path(
    "./data/plugins_data/astrbot_plugin_GPT_SoVITS"
)  # 语音文件保存目录
REFERENCE_AUDIO_DIR: Path = (
    Path(__file__).resolve().parent / "reference_audio"
)  # 参考音频文件目录

SAVED_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
REFERENCE_AUDIO_DIR.mkdir(parents=True, exist_ok=True)


@register(
    "astrbot_plugin_GPT_SoVITS",
    "Zhalslar",
    "GPT_SoVITS对接插件",
    "1.1.9",
    "https://github.com/Zhalslar/astrbot_plugin_GPT_SoVITS",
)
class GPTSoVITSPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        base_setting: Dict = config.get("base_setting", {})
        self.base_url: str = base_setting.get("base_url", "")

        auto_config: Dict = config.get("auto_config", {})
        self.send_record_probability: float = auto_config.get(
            "send_record_probability", 0.15
        )
        self.max_resp_text_len: int = auto_config.get("max_resp_text_len", 50)

        role_config: Dict = config.get("role", {})
        self.default_emotion: str = role_config.get(
            "default_emotion", "生气地"
        )  # 默认情绪预设
        self.gpt_weights_path: str = role_config.get("gpt_weights_path", "")
        self.sovits_weights_path: str = role_config.get("sovits_weights_path", "")
        asyncio.create_task(self._set_model_weights())

        emotions_config = config.get("emotions", {})
        gently_config = emotions_config.get("gently", {})
        happily_config = emotions_config.get("happily", {})
        angrily_config = emotions_config.get("angrily", {})
        surprise_config = emotions_config.get("surprise", {})
        self.preset_emotions: Dict = {
            "温柔地说": {
                "ref_audio_path": gently_config.get("ref_audio_path")
                or str(REFERENCE_AUDIO_DIR / "不要害怕，也不要哭了.wav"),
                "prompt_text": gently_config.get("prompt_text")
                or "不要害怕，也不要哭了",
                "prompt_lang": gently_config.get("prompt_lang"),
                "speed_factor": gently_config.get("speed_factor"),
                "fragment_interval": gently_config.get("fragment_interval"),
            },
            "开心地说": {
                "ref_audio_path": happily_config.get("ref_audio_path")
                or str(REFERENCE_AUDIO_DIR / "它好像在等另一只蕈兽_心情很好的样子.wav"),
                "prompt_text": happily_config.get("prompt_text")
                or "它好像在等另一只蕈兽_心情很好的样子",
                "prompt_lang": happily_config.get("prompt_lang"),
                "speed_factor": happily_config.get("speed_factor"),
                "fragment_interval": happily_config.get("fragment_interval"),
            },
            "生气地说": {
                "ref_audio_path": angrily_config.get("ref_audio_path")
                or str(
                    REFERENCE_AUDIO_DIR
                    / "你还会选择现在的位置吗？到那时，你觉得自己又会是什么呢.wav"
                ),
                "prompt_text": angrily_config.get("prompt_text")
                or "你还会选择现在的位置吗？到那时，你觉得自己又会是什么呢",
                "prompt_lang": angrily_config.get("prompt_lang"),
                "speed_factor": angrily_config.get("speed_factor"),
                "fragment_interval": angrily_config.get("fragment_interval"),
            },
            "惊讶地说": {
                "ref_audio_path": surprise_config.get("ref_audio_path")
                or str(
                    REFERENCE_AUDIO_DIR / "就算是这样，也不至于直接碎掉啊，除非.wav"
                ),
                "prompt_text": surprise_config.get("prompt_text")
                or "就算是这样，也不至于直接碎掉啊，除非",
                "prompt_lang": surprise_config.get("prompt_lang"),
                "speed_factor": surprise_config.get("speed_factor"),
                "fragment_interval": surprise_config.get("fragment_interval"),
            },
        }
        self.preset_emotions_set = set(self.preset_emotions.keys())

        self.keywords_dict = {
            "温柔地说": gently_config.get("keywords"),
            "开心地说": happily_config.get("keywords"),
            "生气地说": angrily_config.get("keywords"),
            "惊讶地说": surprise_config.get("keywords"),
        }

        self.default_params: Dict = config.get("default_params", {})  # 额外参数

    async def _make_request(
        self,
        endpoint: str,
        params=None,
    ) -> None | bytes:
        """通用的异步请求方法"""
        if params:
            params = {
                k: str(v).lower() if isinstance(v, bool) else v
                for k, v in params.items()
            }
        async with aiohttp.ClientSession() as session:
            async with session.request("GET", endpoint, params=params) as response:
                if response.status != 200:
                    return None
                audio_bytes = await response.read()
                return audio_bytes

    async def _set_model_weights(self):
        """设置模型"""
        try:
            # 设置 GPT 模型
            if self.gpt_weights_path:
                gpt_endpoint = f"{self.base_url}/set_gpt_weights"
                gpt_params = {"weights_path": self.gpt_weights_path}
                if await self._make_request(endpoint=gpt_endpoint, params=gpt_params):
                    logger.info(f"成功设置 GPT 模型路径：{self.gpt_weights_path}")
            else:
                logger.info("GPT 模型路径未配置，将使用GPT_SoVITS内置的GPT模型")

            # 设置 SoVITS 模型
            if self.sovits_weights_path:
                sovits_endpoint = f"{self.base_url}/set_sovits_weights"
                sovits_params = {"weights_path": self.sovits_weights_path}
                if await self._make_request(
                    endpoint=sovits_endpoint, params=sovits_params
                ):
                    logger.info(f"成功设置 SoVITS 模型路径：{self.sovits_weights_path}")
            else:
                logger.info("SoVITS 模型路径未配置，将使用GPT_SoVITS内置的SoVITS模型")
        except aiohttp.ClientError as e:
            logger.error(f"设置模型路径时发生错误：{e}")
        except Exception as e:
            logger.error(f"发生未知错误：{e}")

    # 在发送消息前，会触发 on_decorating_result 钩子
    @filter.on_decorating_result()
    async def on_decorating_result(self, event: AstrMessageEvent):
        """将LLM生成的文本按概率生成语音并发送"""
        if random.random() > self.send_record_probability:  # 概率控制
            return

        chain = event.get_result().chain
        seg = chain[0]

        # 仅允许只含有单条文本的消息链通过
        if not (len(chain) == 1 and isinstance(seg, Comp.Plain)):
            return

        resp_text = seg.text  # bot将要发送的的文本

        # 仅允许一定长度以下的文本通过
        if len(resp_text) > self.max_resp_text_len:
            return

        send_text = event.message_str  # 用户发送的文本

        # 根据 ai生成的文本 和 用户发送的文本 匹配关键词，从而选择情绪
        emotion = self.default_emotion
        for emo, keywords in self.keywords_dict.items():
            for keyword in keywords:
                if keyword in send_text or keyword in resp_text:
                    emotion = emo
                    break
            else:
                continue
            break

        params = self.default_params.copy()
        params.update(self.preset_emotions[emotion])  # 传递情绪参数
        params["text"] = resp_text  # 传递文本参数

        file_name = self.generate_file_name(event, params=params)  # 生成文件名
        save_path = await self.tts_inference(
            params=params, file_name=file_name
        )  # 生成语音

        if save_path is None:
            logger.error("TTS任务执行失败！")
            return

        chain.clear()  # 清空消息段
        chain.append(Record.fromFileSystem(save_path))  # 新增语音消息段

    @filter.command(
        "说",
        alias={
            "温柔地说",
            "开心地说",
            "生气地说",
            "惊讶地说",
        },
    )
    async def on_command(
        self, event: AstrMessageEvent, send_text: str | int | None = None
    ):
        """/xx地说 xxx，直接调用TTS，发送合成后的语音"""
        if not send_text:
            yield event.plain_result("未提供文本")
            return
        send_text = str(send_text)
        emotion = next(
            (emo for emo in self.preset_emotions_set if emo in event.get_message_str()),
            self.default_emotion,
        )
        params = self.default_params.copy()
        params.update(self.preset_emotions[emotion])
        params["text"] = send_text

        if not emotion or not send_text:
            return

        file_name = self.generate_file_name(event, params=params)
        save_path = await self.tts_inference(params=params, file_name=file_name)

        if save_path is None:
            logger.error("TTS任务执行失败！")
            return

        chain = [Record.fromFileSystem(save_path)]
        yield event.chain_result(chain)  # type: ignore

    def generate_file_name(self, event: AstrMessageEvent, params) -> str:
        """生成文件名"""
        group_id = event.get_group_id() or "0"
        sender_id = event.get_sender_id() or "0"
        sanitized_text = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff\s]", "", params["text"])
        limit_text = sanitized_text.strip()[:30]  # 限制长度
        media_type = self.default_params["media_type"]
        file_name = f"{group_id}_{sender_id}_{limit_text}.{media_type}"
        return file_name

    async def tts_inference(self, params, file_name: str) -> str | None:
        """发送TTS请求，获取音频内容"""
        endpoint = f"{self.base_url}/tts"
        save_path = str((SAVED_AUDIO_DIR / file_name).resolve())
        audio_bytes = await self._make_request(endpoint=endpoint, params=params)
        if audio_bytes:
            with open(save_path, "wb") as audio_file:
                audio_file.write(audio_bytes)
            return save_path

    @filter.command("重启TTS", alias={"重启tts"})
    async def tts_control(self, event: AstrMessageEvent):
        """重启GPT_SoVITS"""
        yield event.plain_result("重启TTS中...(报错信息请忽略，等待一会即可完成重启)")
        endpoint = f"{self.base_url}/control"
        params = {"command": "restart"}
        await self._make_request(endpoint=endpoint, params=params)

    async def tts_sever(self, text: str, file_name: str) -> str | None:
        """提供给其他插件调用的TTS服务"""
        emotion = self.default_emotion

        # 根据关键词匹配情绪
        for emo, keywords in self.keywords_dict.items():
            for keyword in keywords:
                if keyword in text:
                    emotion = emo
                    break
        params = self.default_params.copy()
        params.update(self.preset_emotions[emotion])
        params["text"] = text

        save_path = await self.tts_inference(params=params, file_name=file_name)
        return save_path
