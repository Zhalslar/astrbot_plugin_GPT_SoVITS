

import os
import re
from datetime import datetime
import random

import requests
from astrbot import logger
from astrbot.api.event import filter
from astrbot.api.star import Context, Star, register
from astrbot.core import AstrBotConfig
from astrbot.core.platform import AstrMessageEvent
import astrbot.api.message_components as Comp
from pathlib import Path
from typing import Dict
from astrbot.api.provider import LLMResponse

SAVED_AUDIO_DIR = Path("./data/GPT_Sovits_data/saved_audio")  # 语音文件保存目录
REFERENCE_AUDIO_DIR: Path =  Path(__file__).resolve().parent / "reference_audio"  # 参考音频文件目录

SAVED_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
REFERENCE_AUDIO_DIR.mkdir(parents=True, exist_ok=True)




@register("astrbot_plugin_GPT_SoVITS", "Zhalslar", "GPT_SoVITS对接插件", "1.0.0", "https://github.com/Zhalslar/astrbot_plugin_GPT_SoVITS")
class GPTSoVITSPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.base_url: str = config.get('base_setting').get('base_url')
        self.save_audio: bool = config.get('base_setting').get("save_audio") # 是否保存合成的音频
        self.save_path = None
        self.send_record_probability: float = config.get('base_setting').get("send_record_probability")  # 发语音的概率

        self.default_emotion: str = config.get('role').get("default_emotion")  # 默认情绪预设
        self.gpt_weights_path: str = config.get('role', {}).get('gpt_weights_path')  # GPT模型文件路径
        self.sovits_weights_path: str = config.get('role', {}).get('sovits_weights_path')  # SoVITS模型文件路径
        self._set_model_weights()

        self.gently_config = config.get('emotions', {}).get('gently', {})
        self.happily_config = config.get('emotions', {}).get('happily', {})
        self.angrily_config = config.get('emotions', {}).get('angrily', {})
        self.surprise_config = config.get('emotions', {}).get('surprise', {})
        self.preset_emotions = {
            "温柔地说": {
                "ref_audio_path": self.gently_config.get('ref_audio_path') or str(REFERENCE_AUDIO_DIR / "不要害怕，也不要哭了.wav"),
                "prompt_text": self.gently_config.get('prompt_text') or "不要害怕，也不要哭了",
                "prompt_lang": self.gently_config.get('prompt_lang'),
                "speed_factor": self.gently_config.get('speed_factor'),
                "fragment_interval": self.gently_config.get('fragment_interval'),
            },
            "开心地说": {
                "ref_audio_path": self.happily_config.get('ref_audio_path') or str(REFERENCE_AUDIO_DIR / "它好像在等另一只蕈兽_心情很好的样子.wav"),
                "prompt_text":  self.gently_config.get('prompt_text') or "它好像在等另一只蕈兽_心情很好的样子",
                "prompt_lang": self.happily_config.get('prompt_lang'),
                "speed_factor": self.happily_config.get('speed_factor'),
                "fragment_interval": self.happily_config.get('fragment_interval'),
            },
            "生气地说": {
                "ref_audio_path": self.angrily_config.get('ref_audio_path') or str(REFERENCE_AUDIO_DIR / "你还会选择现在的位置吗？到那时，你觉得自己又会是什么呢.wav"),
                "prompt_text":  self.gently_config.get('prompt_text') or "你还会选择现在的位置吗？到那时，你觉得自己又会是什么呢",
                "prompt_lang": self.angrily_config.get('prompt_lang'),
                "speed_factor": self.angrily_config.get('speed_factor'),
                "fragment_interval": self.angrily_config.get('fragment_interval'),
            },
            "惊讶地说": {
                "ref_audio_path": self.surprise_config.get('ref_audio_path') or str(REFERENCE_AUDIO_DIR / "就算是这样，也不至于直接碎掉啊，除非.wav"),
                "prompt_text": self.gently_config.get('prompt_text') or "就算是这样，也不至于直接碎掉啊，除非",
                "prompt_lang": self.surprise_config.get('prompt_lang'),
                "speed_factor": self.surprise_config.get('speed_factor'),
                "fragment_interval": self.surprise_config.get('fragment_interval'),
            }
        }
        self.preset_emotions_set = set(self.preset_emotions.keys())


        self.params = config.get('default_params')
        self.default_params: Dict = {
            "ref_audio_path": self.params.get('ref_audio_path',""),  # 参考音频文件路径
            "text": self.params.get('text', ""),  # 要转换的文本
            "text_lang": self.params.get('text_lang', "zh"),  # 文本语言，默认为中文
            "aux_ref_audio_paths": self.params.get('prompt_text', None),   # 辅助参考音频文件路径列表
            "prompt_text": self.params.get('prompt_text', ""),  # 提示文本，用于影响语音合成
            "prompt_lang": self.params.get('prompt_lang', "zh"),  # 提示文本的语言，默认为中文
            "top_k": self.params.get('top_k', 5),  # 控制生成语音的多样性
            "top_p": self.params.get('top_p', 1.0),  # 核采样的阈值
            "temperature": self.params.get('temperature', 1.0),  # 控制生成语音的随机性
            "text_split_method": self.params.get('text_split_method', "cut3"),  # 文本分割的方法
            "batch_size": self.params.get('batch_size', 1),  # 批处理大小
            "batch_threshold": self.params.get('batch_threshold', 0.75),  # 批处理阈值
            "split_bucket": self.params.get('split_bucket', True),  # 是否将文本分割成桶以便并行处理
            "speed_factor": self.params.get('speed_factor', 1),  # 语音播放速度的倍数
            "fragment_interval": self.params.get('fragment_interval', 0.3),  # 语音片段之间的间隔时间
            "streaming_mode": config.get('streaming_mode', False),  # 是否启用流模式
            "seed": self.params.get('seed', -1),  # 随机种子，用于结果的可重复性
            "parallel_infer": self.params.get('parallel_infer', True),  # 是否并行执行推理
            "repetition_penalty": config.get('repetition_penalty', 1.35),  # 重复惩罚因子
            "media_type": self.params.get('media_type', 'wav'),  # 输出媒体的类型
        }

    def _set_model_weights(self):
        """设置模型权重路径"""
        try:
            # 设置 GPT 模型权重
            if self.gpt_weights_path:
                gpt_endpoint = f"{self.base_url}/set_gpt_weights"
                gpt_params = {"weights_path": self.gpt_weights_path}
                response = requests.get(gpt_endpoint, params=gpt_params)
                response.raise_for_status()
                logger.info(f"成功设置 GPT 模型权重路径：{self.gpt_weights_path}")
            else:
                logger.info("GPT 模型权重路径未配置，将使用GPT_SoVITS内置的GPT模型")

            # 设置 SoVITS 模型权重
            if self.sovits_weights_path:
                sovits_endpoint = f"{self.base_url}/set_sovits_weights"
                sovits_params = {"weights_path": self.sovits_weights_path}
                response = requests.get(sovits_endpoint, params=sovits_params)
                response.raise_for_status()
                logger.info(f"成功设置 SoVITS 模型权重路径：{self.sovits_weights_path}")
            else:
                logger.info("SoVITS 模型权重路径未配置，将使用GPT_SoVITS内置的SoVITS模型")
        except requests.RequestException as e:
            logger.error(f"设置模型权重路径时发生错误：{e}")



    async def generate_and_send_tts(self, event: AstrMessageEvent, text: str, emotion: str):
        """生成TTS语音并发送"""
        group_id = event.get_group_id()
        sender_id = event.get_sender_id()

        params = self.default_params.copy()
        params.update(self.preset_emotions[emotion])
        params["text"] = text

        file_name = self.generate_file_name(params=params, group_id=group_id, user_id=sender_id)
        await self.tts_inference(params=params, file_name=file_name)

        if self.save_path is None:
            logger.error("TTS任务执行失败！")
            return

        record = Comp.Record(file=self.save_path)
        result = event.chain_result([record])
        await event.send(result)
        if not self.save_audio:
            os.remove(self.save_path)
        event.stop_event()  # 停止事件传播

    # 在 LLM 请求完成后，触发 on_llm_response 钩子
    @filter.on_llm_response()
    async def on_llm_response(self, event: AstrMessageEvent, resp: LLMResponse):
        """将LLM生成的文本按概率生成语音并发送"""
        if random.random() > self.send_record_probability:
            return

        emotion = self.default_emotion
        text = resp.completion_text

        await self.generate_and_send_tts(event, text, emotion)


    @filter.command("说", alias={"温柔地说", "开心地说", "生气地说", "惊讶地说", })
    async def on_regex(self, event: AstrMessageEvent, text: str = None):
        """xxx说xxx，直接调用TTS，发送合成后的语音"""
        message_str = event.get_message_str()

        emotion = next((emo for emo in self.preset_emotions_set if emo in message_str), self.default_emotion)

        params = self.default_params.copy()
        params.update(self.preset_emotions[emotion])
        params["text"] = text

        yield event.plain_result(f"{params}")

        if not emotion or not text:
            return

        await self.generate_and_send_tts(event, text, emotion)


    def generate_file_name(self, params, group_id: str = "0", user_id: str = "0") -> str:
        """生成文件名"""
        sanitized_text = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff\s]', '', params["text"])
        limit_text = sanitized_text[:30]  # 限制长度
        media_type = self.default_params["media_type"]
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")  # 格式化为年月日_时分秒
        file_name = f"{group_id}_{user_id}_{limit_text}_{current_time}.{media_type}"
        return file_name


    async def tts_inference(self, params, file_name: str = None) -> str | None:
        """发送TTS请求，获取音频内容"""
        endpoint = f"{self.base_url}/tts"
        response = requests.get(endpoint, params=params)
        if response.status_code != 200:
            return None
        audio_bytes: bytes = response.content
        self.save_path = str(SAVED_AUDIO_DIR / file_name)
        with open(self.save_path, 'wb') as audio_file:
            audio_file.write(audio_bytes)
        return self.save_path


    @filter.command("重启TTS", alias={"重启tts"})
    async def tts_control(self,event: AstrMessageEvent):
        yield event.plain_result(f"重启TTS中...(报错信息请忽略，等待一会即可完成重启)")
        endpoint = f"{self.base_url}/control"
        params = {"command": "restart"}
        requests.get(endpoint, params=params)






