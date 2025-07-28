# VRChat 语音翻译插件

一个基于Whisper和AI翻译的VRChat语音翻译插件，支持实时语音识别、AI翻译和VRChat OSC通信。

## 功能特性

- 🎤 **语音识别**：使用Faster-Whisper进行高精度语音转文字
- 🤖 **AI翻译**：集成SiliconFlow API进行中英文翻译
- 🎮 **VRChat集成**：通过OSC协议直接发送到VRChat聊天框
- ⚡ **智能GPU检测**：自动检测GPU显存，智能选择GPU/CPU模式
- ⌨️ **热键控制**：F4键控制录音开始/停止
- 🔊 **音频反馈**：录音开始/停止时播放系统音效
- ⏰ **自动清理**：录音完成后自动删除临时文件

## 系统要求

- Windows 10/11
- Python 3.8+
- 8GB+ RAM
- 可选：NVIDIA GPU (支持CUDA)

## 安装步骤

### 1. 克隆项目
```bash
git clone <项目地址>
cd Qwesen
```

### 2. 安装Python依赖
```bash
py -m pip install -r requirements.txt
```

### 3. 配置API密钥
编辑 `settings.json` 文件，填入你的API配置：
```json
{
  "api_key": "你的API密钥",
  "api_url": "https://api.siliconflow.cn/v1/chat/completions",
  "model": "Pro/deepseek-ai/DeepSeek-V3",
  "speech_engine": "whisper",
  "silence_threshold": 500,
  "silence_duration": 2.0
}
```

### 4. 下载Whisper模型
首次运行时会自动下载模型，或手动下载：
```bash
py -c "from faster_whisper import WhisperModel; WhisperModel('medium')"
```

## 使用方法

### 启动插件
```bash
py VRchat_videoRest.py
```

### 操作说明
1. 启动插件后，会自动发送"STT就绪"到VRChat
2. 按 **F4键** 开始录音
3. 再次按 **F4键** 停止录音
4. 系统自动进行语音识别和翻译
5. 结果发送到VRChat聊天框
6. 10秒后自动发送"STT就绪"提示

### VRChat设置
1. 在VRChat中启用OSC功能
2. 设置OSC接收端口为9000
3. 确保VRChat正在运行

## 配置说明

### GPU/CPU模式
- 系统自动检测GPU显存使用率
- 显存使用率 < 90% 时使用GPU模式
- 显存使用率 ≥ 90% 时自动切换到CPU模式

### 模型选择
- **medium**：平衡准确率和速度（推荐）
- **small**：快速但准确率稍低
- **large-v3**：最高准确率但速度较慢

### 自定义配置
在 `VRchat_videoRest.py` 中修改：
```python
# 修改模型大小
self.whisper_model = WhisperModel("medium", ...)

# 修改显存阈值
if memory_usage_percent < 90:  # 改为你想要的阈值
```

## 故障排除

### 常见问题

1. **"GPU显存充足，使用GPU模式"但实际使用CPU**
   - 检查CUDA是否正确安装
   - 确认PyTorch支持CUDA

2. **录音没有声音**
   - 检查麦克风权限
   - 确认默认录音设备设置

3. **VRChat收不到消息**
   - 确认VRChat OSC功能已启用
   - 检查端口9000是否被占用

4. **API翻译失败**
   - 检查网络连接
   - 确认API密钥和URL正确

### 日志信息
- `GPU显存: X.XGB / X.XGB (XX.X%)`：显示GPU使用情况
- `Whisper模型加载完成`：模型加载状态
- `已发送STT就绪消息`：VRChat通信状态

## 技术架构

```
VRChat语音翻译插件
├── 音频录制 (pyaudio)
├── 语音识别 (faster-whisper)
├── AI翻译 (SiliconFlow API)
├── OSC通信 (python-osc)
└── 智能GPU管理 (pynvml)
```

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 更新日志

### v1.0.0
- 初始版本发布
- 支持Faster-Whisper语音识别
- 集成AI翻译功能
- 智能GPU/CPU切换
- F4热键控制 