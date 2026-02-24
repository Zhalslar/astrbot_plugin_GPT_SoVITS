<div align="center">

![:name](https://count.getloli.com/@astrbot_plugin_GPT_SoVITS?name=astrbot_plugin_GPT_SoVITS&theme=minecraft&padding=6&offset=0&align=top&scale=1&pixelated=1&darkmode=auto)

# astrbot_plugin_GPT_SoVITS

_GPT-SoVITS 对接插件（TTS）_

[![License](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0.html)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![AstrBot](https://img.shields.io/badge/AstrBot-4.0%2B-orange.svg)](https://github.com/Soulter/AstrBot)
[![GitHub](https://img.shields.io/badge/作者-Zhalslar-blue)](https://github.com/Zhalslar)

</div>

---

## 1. 介绍

`astrbot_plugin_GPT_SoVITS` 用于把 AstrBot 文本输出转换成语音输出，底层调用 [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) 的 API。

支持三种调用方式：

1. 指令转语音：手动输入命令立即合成语音。
2. 自动转语音：Bot 正常回复文本时，按概率自动转成语音发出。
3. 工具调用：LLM 工具调用时，GPT-SoVITS 会作为 LLM 工具的 TTS 接口。

此外还支持情绪参数切换（按关键词或 LLM 判别情绪），实现不同语气/语速的播报效果。

---

## 2. 安装

### 2.1 部署 GPT-SoVITS

请先完成 GPT-SoVITS 本体部署：

- 官方仓库：[RVC-Boss/GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS)
- 参考指南：[GPT_SoVITS 指南](https://www.yuque.com/baicaigongchang1145haoyuangong/ib3g1e)

### 2.2 安装 AstrBot 插件

在 AstrBot 插件市场搜索 `astrbot_plugin_GPT_SoVITS` 并安装。

---

## 3. 快速开始

### 3.1 启动 GPT-SoVITS API

Windows 示例（在 GPT-SoVITS 根目录新建 `start_api.bat`）：

```bat
runtime\python.exe api_v2.py
pause
```

或直接命令行启动：

```bash
python api_v2.py
# 或
python3 api_v2.py
```

### 3.2 在 AstrBot 面板配置插件

路径：`插件管理 -> astrbot_plugin_GPT_SoVITS -> 操作 -> 插件配置`

至少确认以下三项：

1. `client.base_url`：GPT-SoVITS API 地址，默认通常是 `http://127.0.0.1:9880`
2. `default_params.ref_audio_path`：参考音频路径（必填，建议先用插件默认值）
3. `enabled`：总开关打开

### 3.3 验证是否可用

在聊天中发送：

```text
说 你好，我是语音测试
```

若收到语音消息，说明链路已打通。

---

## 4. 命令与调用方式

| 命令 | 别名 | 说明 |
| ----- | ----- | ----- |
| `说 <文本>` | `gsv <文本>`、`GSV <文本>` | 手动触发 TTS。成功后音频会保存到插件数据目录 `audio` 文件夹 |
| 概率调用（无命令） | - | Bot 回复阶段按概率自动转语音。触发条件：插件启用、命中概率、消息链全为纯文本、文本长度不超过最大长度 |
| 工具调用（无命令） | LLM Tool | 供模型工具调用的 TTS 接口，由 bot 自行决定是否需要转语音 |
| `重启GSV` | `重启gsv` | 请求 GPT-SoVITS 执行重启 |

---

## 5. 情绪功能说明

插件支持两种情绪参数匹配方式：

1. 关键词匹配：当文本包含某个情绪条目的任一关键词时，使用该条目的语音参数。
2. LLM 判别：开启 `judge.enabled_llm` 后，先让 LLM 判断情绪，再映射到对应条目。

优先级：

1. 若开启 LLM 判别，则优先使用 LLM 结果；
2. 若 LLM 不可用或未匹配成功，则回退到关键词匹配。

首次加载时会自动导入内置情绪条目（如“温柔 / 开心 / 生气”）到 `entry_storage`。

---

## 6. 配置速查

### 6.1 基础配置

| 字段 | 说明 | 建议/取值 |
| --- | --- | --- |
| `enabled` | 插件总开关 | 部署完成后开启 |
| `client.base_url` | GPT-SoVITS API 地址 | 常见为 `http://127.0.0.1:9880` |
| `client.timeout` | API 请求超时时间（秒） | 网络慢或长文本可适当调大 |
| `model.gpt_path` | GPT 权重路径（`.ckpt`） | 可空，空则使用 GPT-SoVITS 当前默认模型 |
| `model.sovits_path` | SoVITS 权重路径（`.pth`） | 可空，空则使用 GPT-SoVITS 当前默认模型 |

### 6.2 自动转语音配置（`auto`）

| 字段 | 说明 | 建议/取值 |
| --- | --- | --- |
| `only_llm_result` | 只处理 LLM 生成的回复 | 建议 `true` |
| `tts_prob` | 自动转语音概率 | `0 ~ 1`，例如 `0.15` |
| `max_msg_len` | 自动转语音的最大文本长度 | 超过该值不转语音 |

### 6.3 默认 TTS 参数（`default_params`）

这些参数会作为每次请求 `/tts` 的默认值：

| 字段 | 说明 | 建议/取值 |
| --- | --- | --- |
| `text` | 默认合成文本 | 手动命令未传文本时会使用 |
| `text_lang` | 目标文本语言 | `zh/en/ja/ko` |
| `ref_audio_path` | 参考音频路径 | 必填，建议先用可用的 `wav` |
| `prompt_text` | 参考音频对应文本 | 建议与参考音频内容一致 |
| `prompt_lang` | 参考文本语言 | 与 `prompt_text` 保持一致 |
| `top_k` / `top_p` / `temperature` | 采样参数 | 控制随机性与稳定性 |
| `speed_factor` | 语速倍率 | `1.0` 为原速 |
| `fragment_interval` | 语句片段间隔（秒） | 值越小节奏越紧凑 |
| `media_type` | 输出音频格式 | `wav/mp3/ogg`（建议 `wav`） |
| `text_split_method` / `batch_size` / `parallel_infer` 等 | 长文本和性能相关参数 | 按显存与效果微调 |

### 6.4 情绪判别配置（`judge` + `entry_storage`）

| 字段 | 说明 | 建议/取值 |
| --- | --- | --- |
| `judge.enabled_llm` | 是否启用 LLM 判别情绪 | 不开则仅走关键词匹配 |
| `judge.provider_id` | 用于情绪判别的模型提供商 ID | 留空时跟随当前会话模型 |
| `entry_storage[].name` | 情绪名称 | 建议唯一，便于识别 |
| `entry_storage[].keywords` | 触发关键词列表 | 文本包含任一关键词即命中 |
| `entry_storage[].ref_audio_path` | 该情绪使用的参考音频 | 可与默认参考音频不同 |
| `entry_storage[].prompt_text/prompt_lang` | 该参考音频对应文本和语言 | 建议准确填写 |
| `entry_storage[].speed_factor/fragment_interval` | 该情绪下语速与间隔 | 用于塑造语气差异 |

---

## 7. 常见问题与排查

### 7.1 提示“合成失败”

优先检查：

1. GPT-SoVITS API 是否已启动；
2. `client.base_url` 是否正确；
3. `default_params.ref_audio_path` 文件是否存在；
4. GPT-SoVITS 控制台是否有报错信息。

### 7.2 自动模式没有触发

常见原因：

1. `tts_prob` 太低；
2. 回复文本超过 `max_msg_len`；
3. 回复里包含图片/语音等非纯文本片段；
4. `only_llm_result=true` 且该消息不是 LLM 输出。

### 7.3 情绪没有切换

1. 若使用关键词模式，确认关键词确实出现在回复文本中；
2. 若使用 LLM 模式，确认 `judge.provider_id` 可用且返回格式正确；
3. 确认目标情绪条目名称存在于 `entry_storage`。

---

## 👥 贡献指南

- 🌟 Star 这个项目！（点右上角的星星，感谢支持！）
- 🐛 提交 Issue 报告问题
- 💡 提出新功能建议
- 🔧 提交 Pull Request 改进代码

## 📌 注意事项

- 本插件优先兼容 GPT-SoVITS 官方实现与常见整合包。若使用第三方魔改版本，请以其 API 实际行为为准。
- 想第一时间得到反馈的可以来作者的插件反馈群（QQ群）：460973561（不点star不给进）


## 🙏 致谢

[GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS)， 1 min voice data can also be used to train a good TTS model! (few shot voice cloning)
