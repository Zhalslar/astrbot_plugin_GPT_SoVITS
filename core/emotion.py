import json
from astrbot.api import logger
from astrbot.core.platform.astr_message_event import AstrMessageEvent

from .config import PluginConfig


class EmotionJudger:
    def __init__(self, config: PluginConfig):
        self.cfg = config

    async def judge_emotion(
        self,
        event: AstrMessageEvent,
        *,
        text: str = "",
        image_urls: list[str] | None = None,
        labels: list[str] | None = None,
    ) -> str | None:
        """
        使用 LLM 判断文本情感并返回情感标签。

        对外行为约定：
        - 本方法 **不会抛出异常**，失败时返回 None
        - 若 event.extra 中已存在 emotion，则直接复用（避免重复调用 LLM）
        - 成功解析后会将 emotion 写入 event.extra，供后续流程复用

        :param event: AstrBot 消息事件
        :param text: 需要进行情感分析的文本
        :param image_urls: 可选的图片 URL（用于多模态模型）
        :param labels:
            - 指定可选的情感标签列表（如 ["开心", "愤怒", "悲伤"]）
            - 为空或 None 表示 **不限制情感标签**
        :return:
            - 成功时返回情感标签字符串
            - 失败时返回 None
        """
        if cached:= event.get_extra("emotion"):
            if (labels and cached in labels) or (not labels):
                logger.debug(f"复用情感标签: {cached}")
                return cached
        try:
            provider = self.cfg.get_judge_provider(event.unified_msg_origin)
            system_prompt, prompt = self._build_prompt(text, labels)

            resp = await provider.text_chat(
                system_prompt=system_prompt,
                prompt=prompt,
                image_urls=image_urls,
            )

            emotion = self._parse_llm_response(resp.completion_text)
            logger.debug(f"情感分析结果: {emotion}")

            event.set_extra("emotion", emotion)
            return emotion

        except Exception as e:
            logger.exception(f"情感分析失败: {e}")
            return None

    def _build_prompt(
        self,
        text: str,
        labels: list[str] | None,
    ) -> tuple[str, str]:
        if labels:
            label_hint = f"只能从以下情感标签中选择一个：{labels}\n"
        else:
            label_hint = (
                "不限制情感标签，请自行判断文本的主要情感。\n"
                "情感应为简短、常见、可概括的情感词\n"
            )

        system_prompt = (
            "你是一个情感分析专家。\n"
            f"{label_hint}"
            "请严格按照 JSON 格式输出，不要包含任何多余内容。\n"
            '输出示例：{"emotion": "开心"}'
        )

        prompt = f"文本内容：{text}"
        return system_prompt, prompt

    def _parse_llm_response(self, text: str) -> str:
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM 返回非 JSON: {text}") from e

        emotion = data.get("emotion")
        if not emotion or not isinstance(emotion, str):
            raise ValueError(f"LLM JSON 缺少或非法 emotion 字段: {data}")

        return emotion
