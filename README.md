# astrbot_plugin_GPT_SoVITS

## 介绍

**astrbot_plugin_GPT_SoVITS** 是一个 astrbot 插件，用于对接 [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS)，该插件实现了 TTS（文本到语音）的功能。


## 📦 安装

- 第一步，本地部署 GPT_SoVITS（安装包大约5G，装完后10G以上）、
- 本人用的是B站up主做的整合包: [2小时轻松入门GPT-SoVITS，包含整合包，autodl，colab教程，搭配文档观看](https://www.bilibili.com/video/BV1GJ4m1e7x2/?share_source=copy_web&vd_source=b3e26d110d9269b5607f8a2e9ffb7345)
- 安装过程遇到的各种问题，如非本插件范畴内，请自行解决

- 第二步，安装本插件
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
![tmpE999](https://github.com/user-attachments/assets/2f101895-a28f-45d7-8707-84f46ea3d990)


## 🐔 使用说明
- 正常聊天，有概率自动触发LLM文本转语音，概率可在配置里更改

- `{emotion} {text}` - 生成语音，emotion为情绪，text为文本
- `惊讶地说 怎么啦？` - 示例1，注意用空格隔空参数
- `生气地说 我再也不理你了` - 示例2，注意用空格隔空参数

## 📌 注意事项
GPT_SoVITS的部署目前我仅在Windows11下测试过，并成功部署，更多环境下的部署请看[GPT_SoVITS官方文档](https://github.com/RVC-Boss/GPT-SoVITS/blob/main/docs/cn/README.md)
或者本人用的[整合包文档](https://www.yuque.com/xter/zibxlp/nqi871glgxfy717e#)


## 📌 TODO
- 适配GPT_SoVITS_v3
- 测试更多环境下的部署

## 📜 开源协议
本项目采用 [MIT License](LICENSE)

