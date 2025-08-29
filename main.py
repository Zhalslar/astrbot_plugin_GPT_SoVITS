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
from typing import Dict, Any # 1. 导入 Any


SAVED_AUDIO_DIR = Path(
    "./data/plugins_data/astrbot_plugin_GPT_SoVITS"
)
REFERENCE_AUDIO_DIR: Path = (
    Path(__file__).resolve().parent / "reference_audio"
)

SAVED_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
REFERENCE_AUDIO_DIR.mkdir(parents=True, exist_ok=True)


@register(
    "astrbot_plugin_GPT_SoVITS",
    "Zhalslar",
    "GPT_SoVITS对接插件",
    "1.2.0", # 建议更新一下版本号
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
        )
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
        self.default_params: Dict = config.get("default_params", {})

    # --- START OF MODIFIED CODE ---

    async def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: Dict[str, Any] | None = None,
        json_data: Dict[str, Any] | None = None,
    ) -> None | bytes:
        """
        通用的异步请求方法，现在支持GET和POST。
        - params: 用于GET请求的URL查询参数。
        - json_data: 用于POST请求的JSON请求体。
        """
        # 对布尔值进行预处理
        payload = params or json_data
        if payload:
            payload = {
                k: str(v).lower() if isinstance(v, bool) else v
                for k, v in payload.items()
            }
            if method.upper() == "POST":
                json_data = payload
                params = None
            else:
                params = payload
                json_data = None
        
        headers = {'Content-Type': 'application/json'} if method.upper() == "POST" else None

        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                # 使用 session.request 动态选择方法
                async with session.request(
                    method.upper(), endpoint, params=params, json=json_data
                ) as response:
                    response.raise_for_status() # 如果状态码不是2xx，则抛出异常
                    content = await response.read()
                    return content
            except aiohttp.ClientError as e:
                logger.error(f"Request to {endpoint} failed: {e}")
                return None

    # ... (on_decorating_result 和 on_command 保持不变) ...
    
    async def tts_inference(self, params, file_name: str) -> str | None:
        """发送TTS请求，获取音频内容"""
        endpoint = f"{self.base_url}/tts"
        save_path = str((SAVED_AUDIO_DIR / file_name).resolve())
        
        # --- 关键修改：明确使用POST方法，并将params作为json_data传递 ---
        audio_bytes = await self._make_request(
            endpoint=endpoint, 
            method="POST",       # 指定方法为 POST
            json_data=params     # 指定负载为 JSON Body
        )
        
        if audio_bytes:
            with open(save_path, "wb") as audio_file:
                audio_file.write(audio_bytes)
            return save_path

    # --- END OF MODIFIED CODE ---
    
    # ... (从 _set_model_weights 到文件结尾的所有其他函数都保持不变) ...
    
    async def _set_model_weights(self):
        """设置模型"""
        try:
            if self.gpt_weights_path:
                gpt_endpoint = f"{self.base_url}/set_gpt_weights"
                gpt_params = {"weights_path": self.gpt_weights_path}
                if await self._make_request(endpoint=gpt_endpoint, params=gpt_params):
                    logger.info(f"成功设置 GPT 模型路径：{self.gpt_weights_path}")
            else:
                logger.info("GPT 模型路径未配置，将使用GPT_SoVITS内置的GPT模型")
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

    @filter.on_decorating_result()
    async def on_decorating_result(self, event: AstrMessageEvent):
        if random.random() > self.send_record_probability:
            return
        chain = event.get_result().chain
        seg = chain[0]
        if not (len(chain) == 1 and isinstance(seg, Comp.Plain)):
            return
        resp_text = seg.text
        if len(resp_text) > self.max_resp_text_len:
            return
        send_text = event.message_str
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
        params.update(self.preset_emotions[emotion])
        params["text"] = resp_text
        file_name = self.generate_file_name(event, params=params)
        save_path = await self.tts_inference(
            params=params, file_name=file_name
        )
        if save_path is None:
            logger.error("TTS任务执行失败！")
            return
        chain.clear()
        chain.append(Record.fromFileSystem(save_path))

    @filter.command(
        "说",
        alias={
            "温柔地说", "开心地说", "生气地说", "惊讶地说",
        },
    )
    async def on_command(
        self, event: AstrMessageEvent, send_text: str | int | None = None
    ):
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
        yield event.chain_result(chain)

    def generate_file_name(self, event: AstrMessageEvent, params) -> str:
        group_id = event.get_group_id() or "0"
        sender_id = event.get_sender_id() or "0"
        sanitized_text = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff\s]", "", params["text"])
        limit_text = sanitized_text.strip()[:30]
        media_type = self.default_params["media_type"]
        file_name = f"{group_id}_{sender_id}_{limit_text}.{media_type}"
        return file_name

    @filter.command("重启TTS", alias={"重启tts"})
    async def tts_control(self, event: AstrMessageEvent):
        yield event.plain_result("重启TTS中...(报错信息请忽略，等待一会即可完成重启)")
        endpoint = f"{self.base_url}/control"
        params = {"command": "restart"}
        await self._make_request(endpoint=endpoint, params=params)

    async def tts_sever(self, text: str, file_name: str) -> str | None:
        emotion = self.default_emotion
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
