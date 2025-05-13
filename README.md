
<div align="center">

![:name](https://count.getloli.com/@astrbot_plugin_GPT_SoVITS?name=astrbot_plugin_GPT_SoVITS&theme=minecraft&padding=6&offset=0&align=top&scale=1&pixelated=1&darkmode=auto)

# astrbot_plugin_GPT_SoVITS

_✨ [astrbot](https://github.com/AstrBotDevs/AstrBot) GPT_SoVITS对接插件 ✨_  

[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![AstrBot](https://img.shields.io/badge/AstrBot-3.4%2B-orange.svg)](https://github.com/Soulter/AstrBot)
[![GitHub](https://img.shields.io/badge/作者-Zhalslar-blue)](https://github.com/Zhalslar)

</div>

## 🐔 介绍

**astrbot_plugin_GPT_SoVITS** 是一个 astrbot 插件，用于对接 [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS)，该插件实现了 TTS（文本到语音）的功能。

## 📦 安装

### 第一步，本地部署 GPT_SoVITS、

- 安装步骤请看[GPT_SoVITS仓库](https://github.com/RVC-Boss/GPT-SoVITS)（安装包6G+，装完后10G+）
- 配合[GPT_SoVITS指南](https://www.yuque.com/baicaigongchang1145haoyuangong/ib3g1e)来看

### 第二步，安装本插件

- 可以直接在astrbot的插件市场搜索astrbot_plugin_GPT_SoVITS，点击安装，耐心等待安装完成即可  

- 或者可以直接克隆源码到插件文件夹：

```bash
# 克隆仓库到插件目录
cd /AstrBot/data/plugins
git clone https://github.com/Zhalslar/astrbot_plugin_GPT_SoVITS 

# 控制台重启AstrBot
```

## ⚙️ 配置

请在astrbot面板配置，插件管理 -> astrbot_plugin_memelite -> 操作 -> 插件配置
![tmpDD79](https://github.com/user-attachments/assets/4155ee85-c308-4775-89a8-615fd3d0c5d0)

- GPT-SoVITS API 的 URL(base_url)：必填！GPT_SoVITS官方整合包默认为<http://127.0.0.1:9880，> 第三方整合包可能不同
- GPT模型文件路径(gpt_weights_path)：即“.ckpt”后缀的文件，请使用绝对路径！路径两端不要带双引号！！不填则默认用GPT_SoVITS内置的GPT模型
- SoVITS模型文件路径(sovits_weights_path)：即“.pth”后缀的文件，请使用绝对路径，路径两端不要带双引号！！不填则默认用GPT_SoVITS内置的SoVITS模型
- 默认使用的情绪(default_emotion)：内置情绪有：温柔地说、开心地说、惊讶地说、生气地说，每种情绪都可以自定义，如下图
![图片](https://github.com/user-attachments/assets/475aecd6-1b20-47da-9f3a-6b18fda35f3d)

## 🐔 使用说明

### 第一步，启动GPT_SoVITS的API服务  

- Windows下，编写一个bat批处理文件放在GPT_SoVITS整合包的根目录里，文件内容：

```bash
runtime\python.exe api_v2.py
pause
```

然后双击bat文件即可在终端启动GPT_SoVITS的API服务
![tmpAC40](https://github.com/user-attachments/assets/d07f59a0-7a97-478b-99b0-2ef3d207be3f)

- Windows或者Linux下，可以直接通过命令行启动GPT_SoVITS的API服务，比如：

```bash
python api_v2.py
也可能是
python3 api_v2.py

```

### 第二步，调用

- 自动调用：调用LLM得到的文本有概率会自动转成语音发送，概率可在配置里调
- 指令调用：

```bash
 /{emotion} {text}` # 生成语音，emotion为情绪，text为文本
/说 怎么啦？ # 示例1，使用默认情绪，注意用空格隔空参数
/生气地说 我再也不理你了 # 示例2，使用指定情绪，注意用空格隔空参数
```

## 🤝 TODO

- [x] 对接GPT_SoVITS,实现基本TTS的功能
- [x] bot发送消息前，一定概率自动触发TTS
- [x] 支持多情绪，并自动切换
- [ ] 支持多模型
- [ ] 支持多语言自动处理
- [ ] 改成astrbot服务商，内嵌在astrbot框架中

## 👥 贡献指南

- 🌟 Star 这个项目！（点右上角的星星，感谢支持！）
- 🐛 提交 Issue 报告问题
- 💡 提出新功能建议
- 🔧 提交 Pull Request 改进代码

## 📌 注意事项

- 本项目优先兼容官方整合包，第三方整合包只要不是大改的基本也能对接
- GPT_SoVITS的部署目前我仅测试了Windows环境，更多环境下的部署请自行查阅[GPT_SoVITS官方文档](https://github.com/RVC-Boss/GPT-SoVITS/blob/main/docs/cn/README.md)
- 想第一时间得到反馈的可以来作者的插件反馈群（QQ群）：460973561（不点star不给进）
