# astrbot_plugin_GPT_SoVITS

## 介绍

**astrbot_plugin_GPT_SoVITS** 是一个 astrbot 插件，用于对接 [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS)，该插件实现了 TTS（文本到语音）的功能。

## 使用方法

### 指令说明：

- `{gpt_sovits_command} [text] [-e emotion] [-l language]` - 生成语音，支持可选情绪和语言
- `gptsovits帮助` - 显示帮助信息

### 示例：

- `{gpt_sovits_command} 你好` - 生成语音
- `{gpt_sovits_command} 你好 -e 1` - 使用情绪编号 1 生成语音
- `{gpt_sovits_command} hello -e 1 -l en` - 以情绪编号 1 生成一段英文语音

**可选语言**：中文、英文、日文、中英混合、日英混合、多语种混合

> `gpt_sovits_command` 和 `emotion` 参数取决于配置文件中的设置

## 📦 安装

- 第一步，安装 meme-generator  
- 在astrbot控制台或进到astrbot的虚拟环境里，运行下面的命令，耐心等待安装完成，
- 如果是docker部署的astrbot，还需挂载meme-generator到astrbot的虚拟环境里，具体怎么做我还没测
```
pip install meme-generator
```

## ⚙️ 配置

在 `.env` 文件中添加以下配置：

| 配置项                   | 默认值                     | 说明 |
| ------------------------ | -------------------------- | --- |
| GPT_SOVITS_API_BASE_URL   | http://127.0.0.1:9880       | 可选。GPT-SoVITS API 的 URL |
| GPT_SOVITS_API_V2         | True                        | 可选。是否使用 GPT-SoVITS API v2。注意：API 是否为 v2 不取决于你使用的 GPT-SoVITS 模型版本，而是由你运行的 API 脚本决定。`api_v2.py` 为 API v2，`api.py` 为 API v1 |
| GPT_SOVITS_COMMAND        | tts                         | 可选。触发 TTS 的命令，可自定义为 GPT-SoVITS 角色名 |
| GPT_SOVITS_CONVERT_TO_SILK| False                       | 可选。是否将生成音频转换为 SILK 格式发送 |
| GPT_SOVITS_EMOTION_MAP    | 无默认值                     | 必填。配置情感映射 |
| GPT_SOVITS_ARGS           | 无默认值                     | 可选。传递给 GPT-SoVITS 的额外参数，如 `{"temperature": 0.9}` |

### GPT_SOVITS_EMOTION_MAP 示例配置：

```json
[
  {
    "name": "平静",
    "sentences": [
      {"text": "示例文本1", "language": "zh", "path": "路径1"},
      {"text": "示例文本2", "language": "zh", "path": "路径2"}
    ]
  },
  {
    "name": "激动",
    "sentences": [
      {"text": "示例文本3", "language": "zh", "path": "路径3"}
    ]
  }
]
```

### TTS合成的默认参数 配置说明

一般不需要配置此项，但如果你需要传递额外参数给 GPT-SoVITS，  
请在astrbot面板配置，插件管理 -> astrbot_plugin_memelite -> 操作 -> 插件配置 -> default_tts_params。


## 🐔 使用说明
无


## 📌 注意事项
无


## 📜 开源协议
本项目采用 [MIT License](LICENSE)

