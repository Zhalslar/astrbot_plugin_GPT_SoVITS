import re
from datetime import datetime
import requests
from astrbot import logger
from astrbot.api.event import filter
from astrbot.api.star import Context, Star, register
from astrbot.core import AstrBotConfig
from astrbot.core.platform import AstrMessageEvent
import astrbot.api.message_components as Comp
from pathlib import Path
from typing import Dict


SAVED_AUDIO_DIR = Path("./data/GPT_Sovits_data/saved_audio")  # 语音文件保存目录
REFERENCE_AUDIO_DIR: Path =  Path(__file__).resolve().parent / "reference_audio"  # 参考音频文件目录

SAVED_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
REFERENCE_AUDIO_DIR.mkdir(parents=True, exist_ok=True)


preset_emotion: Dict = {
    "温柔地": {
        "ref_audio_path": REFERENCE_AUDIO_DIR / "不要害怕，也不要哭了.wav",
        "prompt_text": "不要害怕，也不要哭了",
        "prompt_lang": "zh",
        "speed_factor": 1,
        "fragment_interval": 0.7,
    },
    "开心地": {
        "ref_audio_path": REFERENCE_AUDIO_DIR / "它好像在等另一只蕈兽_心情很好的样子.wav",
        "prompt_text": "它好像在等另一只蕈兽，心情很好的样子",
        "prompt_lang": "zh",
        "speed_factor": 1.1,
        "fragment_interval": 0.3,
    },
    "生气地": {
        "ref_audio_path": REFERENCE_AUDIO_DIR / "你还会选择现在的位置吗？到那时，你觉得自己又会是什么呢.wav",
        "prompt_text": "你还会选择现在的位置吗？到那时，你觉得自己又会是什么呢",
        "prompt_lang": "zh",
        "speed_factor": 1.2,
        "fragment_interval": 0.5,
    },
    "惊讶地": {
        "ref_audio_path": REFERENCE_AUDIO_DIR / "就算是这样，也不至于直接碎掉啊，除非.wav",
        "prompt_text": "就算是这样，也不至于直接碎掉啊，除非",
        "prompt_lang": "zh",
        "speed_factor": 1,
        "fragment_interval": 0.6,
    }
}



@register("astrbot_plugin_GPT_Sovits", "Zhalslar", "GPT_Sovits对接插件", "1.0.0", "https://github.com/Zhalslar/astrbot_plugin_GPT_SoVITS")
class HelpPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.base_url: str = config.get('base_url',"http://127.0.0.1:9880")
        self.default_emotion: str =  config.get("default_emotion","惊讶地")  # 默认语气预设
        self.default_text: str =  config.get("default_text","说什么呀？")  # 默认使用的文本
        self.save_audio: bool = config.get("save_audio", False) # 是否保存合成的音频
        self.default_tts_params: Dict = {
            "ref_audio_path": config.get('ref_audio_path',""),  # 参考音频文件路径
            "text": config.get('text', ""),  # 要转换的文本
            "text_lang": config.get('text_lang', "zh"),  # 文本语言，默认为中文
            "aux_ref_audio_paths": config.get('prompt_text', None),   # 辅助参考音频文件路径列表
            "prompt_text": config.get('prompt_text', ""),  # 提示文本，用于影响语音合成
            "prompt_lang": config.get('prompt_lang', "zh"),  # 提示文本的语言，默认为中文
            "top_k": config.get('top_k', 5),  # 控制生成语音的多样性
            "top_p": config.get('top_p', 1.0),  # 核采样的阈值
            "temperature": config.get('temperature', 1.0),  # 控制生成语音的随机性
            "text_split_method": config.get('text_split_method', "cut3"),  # 文本分割的方法
            "batch_size": config.get('batch_size', 1),  # 批处理大小
            "batch_threshold": config.get('batch_threshold', 0.75),  # 批处理阈值
            "split_bucket": config.get('split_bucket', True),  # 是否将文本分割成桶以便并行处理
            "speed_factor": config.get('speed_factor', 1),  # 语音播放速度的倍数
            "fragment_interval": config.get('fragment_interval', 0.3),  # 语音片段之间的间隔时间
            "streaming_mode": config.get('streaming_mode', False),  # 是否启用流模式
            "seed": config.get('seed', -1),  # 随机种子，用于结果的可重复性
            "parallel_infer": config.get('parallel_infer', True),  # 是否并行执行推理
            "repetition_penalty": config.get('repetition_penalty', 1.35),  # 重复惩罚因子
            "media_type": config.get('media_type', 'wav'),  # 输出媒体的类型
        }


    @filter.regex("^(.*?)(说)(.*)$")
    async def on_regex(self, event: AstrMessageEvent):
        """xxx说xxx，直接调用TTS，发送合成后的语音"""
        group_id = event.get_group_id()
        sender_id = event.get_sender_id()
        message_str = event.get_message_str()
        pattern = "^(.*?)(说)(.*)$"
        match = re.match(pattern=pattern, string=message_str, flags=re.DOTALL)
        if not match:
            return
        emotion = match.group(1).strip()  # 语气词
        text = match.group(3).strip()  # 需要转成语音的文本

        target_emotion = emotion if (emotion and emotion in preset_emotion) else self.default_emotion
        target_text = text if text else self.default_text

        params = self.default_tts_params.copy()
        logger.info(f"参数：{params}")
        params.update(preset_emotion[target_emotion])
        params["text"] = target_text

        logger.info(
            f"\nTTS任务开启："
            f"\n群号：{group_id}"
            f"\n发起者：{sender_id}"
            f"\n语气词：{target_emotion}"
            f"\n目标文本：{target_text}"
        )
        file_name = self.generate_file_name(params=params, group_id=group_id, user_id=sender_id)
        file_path = await self.tts_run(params=params, file_name=file_name)

        if file_path is None:
            logger.error("TTS任务执行失败！")
            return

        # 以语音形式发送
        record = Comp.Record(file=file_path)
        yield event.chain_result([record])



    def generate_file_name(self, params, group_id: str = "0", user_id: str = "0") -> str:
        """生成文件名"""
        sanitized_text = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff\s]', '', params["text"])
        limit_text = sanitized_text[:30]  # 限制长度
        media_type = self.default_tts_params["media_type"]
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")  # 格式化为年月日_时分秒
        file_name = f"{group_id}_{user_id}_{limit_text}_{current_time}.{media_type}"
        return file_name


    async def tts_run(self, params, file_name: str = None) -> str | None:
        """发送TTS请求，获取音频内容"""
        print(params)
        response = requests.get(self.base_url, params=params)
        if response.status_code != 200:
            return None
        audio_bytes: bytes = response.content
        file_path = SAVED_AUDIO_DIR / file_name
        with open(file_path, 'wb') as audio_file:
            audio_file.write(audio_bytes)
        return str(file_path)













