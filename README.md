# astrbot_plugin_GPT_SoVITS

## 介绍

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


## 🐔 使用说明
### 第一步，启动GPT_SoVITS的API服务
![tmpAC40](https://github.com/user-attachments/assets/d07f59a0-7a97-478b-99b0-2ef3d207be3f)

### 第二步，正常使用
- `{emotion} {text}` - 生成语音，emotion为情绪，text为文本
- `惊讶地说 怎么啦？` - 示例1，注意用空格隔空参数
- `生气地说 我再也不理你了` - 示例2，注意用空格隔空参数

## 📌 注意事项
- 本项目优先兼容官方整合包，第三方整合包只要不是大改的基本也能对接
- GPT_SoVITS的部署目前我仅测试了Windows环境，更多环境下的部署请自行查阅[GPT_SoVITS官方文档](https://github.com/RVC-Boss/GPT-SoVITS/blob/main/docs/cn/README.md)
- 想第一时间得到反馈的可以来作者的插件反馈群（QQ群）：460973561

## TODO
- 测试更多环境下的部署

## 📜 开源协议
本项目采用 [MIT License](LICENSE)



