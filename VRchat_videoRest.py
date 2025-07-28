#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VRChat 语音翻译插件
简洁版本 - 空格键控制录音
"""

import os
import time
import threading
import json
import keyboard
import pyaudio
import wave
import winsound
import requests
from datetime import datetime
from faster_whisper import WhisperModel
from pythonosc.udp_client import SimpleUDPClient

# 备用STT服务
try:
    import speech_recognition as sr
    GOOGLE_STT_AVAILABLE = True
except ImportError:
    GOOGLE_STT_AVAILABLE = False

# GPU检测
try:
    import torch
    import pynvml
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False

class VRChatVoiceTranslator:
    def __init__(self):
        # 加载配置
        self.load_settings()
        
        # 录音参数
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.chunk = 1024
        
        # 状态控制
        self.is_recording = False
        self.recording_thread = None
        self.audio = pyaudio.PyAudio()
        
        # 录音计数器
        self.recording_count = 0
        
        # VRChat OSC客户端
        self.vrchat_client = SimpleUDPClient("127.0.0.1", 9000)
        
        # 定时器
        self.ready_timer = None
        
        # 检测GPU并初始化Whisper模型
        self.init_whisper_model()
        
        print("=== VRChat 语音翻译插件 ===")
        print("按F4键开始/停止录音")
        print("按 Ctrl+C 退出程序")
        
        # 发送初始STT就绪消息
        self.send_stt_ready()
    
    def check_gpu_memory(self):
        """检查GPU显存使用情况"""
        if not GPU_AVAILABLE:
            return False, 0
        
        try:
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            
            total_memory = info.total / 1024**3  # GB
            used_memory = info.used / 1024**3    # GB
            memory_usage_percent = (used_memory / total_memory) * 100
            
            print(f"GPU显存: {used_memory:.1f}GB / {total_memory:.1f}GB ({memory_usage_percent:.1f}%)")
            
            # 如果显存使用率低于90%（剩余10%），使用GPU
            if memory_usage_percent < 90:
                return True, memory_usage_percent
            else:
                return False, memory_usage_percent
                
        except Exception as e:
            print(f"GPU检测失败: {e}")
            return False, 0
    
    def init_whisper_model(self):
        """初始化Whisper模型，根据GPU显存情况选择设备"""
        print("正在检测GPU显存使用情况...")
        
        use_gpu, memory_usage = self.check_gpu_memory()
        
        if use_gpu and torch.cuda.is_available():
            print("GPU显存充足，使用GPU模式")
            self.whisper_model = WhisperModel(
                "medium", 
                device="cuda", 
                compute_type="float16",
                download_root=None
            )
            print("Whisper模型加载完成 (medium, GPU模式)")
        else:
            if not torch.cuda.is_available():
                print("CUDA不可用，使用CPU模式")
            else:
                print(f"GPU显存使用率过高 ({memory_usage:.1f}%)，剩余显存不足10%，使用CPU模式")
            
            self.whisper_model = WhisperModel(
                "medium", 
                device="cpu", 
                compute_type="int8",
                cpu_threads=8
            )
            print("Whisper模型加载完成 (medium, CPU模式)")
    
    def setup_keyboard_listener(self):
        """设置键盘监听"""
        def on_f4_press(e):
            if e.name == 'f4':
                if not self.is_recording:
                    # 开始录音
                    self.start_recording()
                else:
                    # 停止录音
                    self.stop_recording()
        
        # 注册键盘事件
        keyboard.on_press(on_f4_press)
        print("键盘监听已设置")
    
    def load_settings(self):
        """加载配置文件"""
        try:
            with open("settings.json", "r", encoding="utf-8") as f:
                settings = json.load(f)
                self.api_key = settings.get("api_key", "")
                self.api_url = settings.get("api_url", "")
                self.model = settings.get("model", "")
                print("配置文件加载成功")
        except Exception as e:
            print(f"配置文件加载失败: {e}")
            self.api_key = ""
            self.api_url = ""
            self.model = ""
    
    def send_stt_ready(self):
        """发送STT就绪消息到VRChat"""
        try:
            self.vrchat_client.send_message("/chatbox/input", ["STT就绪", True])
            print("已发送STT就绪消息")
        except Exception as e:
            print(f"发送STT就绪消息失败: {e}")
    
    def start_ready_timer(self):
        """启动10秒后发送STT就绪的定时器"""
        if self.ready_timer:
            self.ready_timer.cancel()
        self.ready_timer = threading.Timer(10.0, self.send_stt_ready)
        self.ready_timer.daemon = True
        self.ready_timer.start()
    
    def start_recording(self):
        """开始录音"""
        if not self.is_recording:
            self.is_recording = True
            self.recording_count += 1
            print(f"\n=== 开始录音 #{self.recording_count} ===")
            
            # 播放开始音效
            try:
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            except:
                pass
            
            # 启动录音线程
            self.recording_thread = threading.Thread(target=self.record_audio)
            self.recording_thread.daemon = True
            self.recording_thread.start()
    
    def stop_recording(self):
        """停止录音"""
        if self.is_recording:
            self.is_recording = False
            print("=== 停止录音 ===")
            
            # 播放停止音效
            try:
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            except:
                pass
            
            # 等待录音线程结束
            if self.recording_thread:
                self.recording_thread.join(timeout=2)
    
    def record_audio(self):
        """录音功能"""
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{self.recording_count}_{timestamp}.wav"
        
        print(f"录音文件: {filename}")
        
        # 打开音频流
        stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk
        )
        
        frames = []
        frame_count = 0
        
        try:
            print("开始录音...")
            while self.is_recording:
                data = stream.read(self.chunk)
                frames.append(data)
                frame_count += 1
                
                # 每50帧显示一次进度
                if frame_count % 50 == 0:
                    duration = frame_count * self.chunk / self.rate
                    print(f"录音中... {duration:.1f}秒")
                
                time.sleep(0.001)  # 1ms延迟
                
        except Exception as e:
            print(f"录音出错: {e}")
        finally:
            # 关闭音频流
            stream.stop_stream()
            stream.close()
            
            # 保存录音文件
            if frames:
                self.save_audio(frames, filename)
                duration = len(frames) * self.chunk / self.rate
                print(f"录音完成: {filename} ({duration:.2f}秒)")
                
                # 进行语音识别
                self.transcribe_audio(filename)
            else:
                print("录音数据为空")
    
    def save_audio(self, frames, filename):
        """保存音频文件"""
        try:
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.format))
                wf.setframerate(self.rate)
                wf.writeframes(b''.join(frames))
            print(f"文件已保存: {filename}")
        except Exception as e:
            print(f"保存文件失败: {e}")
    
    def transcribe_audio(self, filename):
        """使用Whisper转录音频"""
        try:
            print(f"开始语音识别: {filename}")
            
            # 使用Whisper转录音频
            segments, info = self.whisper_model.transcribe(filename, language="zh")
            
            # 合并所有片段
            text = " ".join([segment.text for segment in segments]).strip()
            
            if text:
                print(f"识别结果: {text}")
                print(f"语言: {info.language}, 置信度: {info.language_probability:.2f}")
                
                # 进行AI翻译
                self.translate_and_send(text)
            else:
                print("未识别到语音内容")
                # 启动10秒定时器
                self.start_ready_timer()
            
            # 删除录音文件
            try:
                os.remove(filename)
                print(f"录音文件已删除: {filename}")
            except Exception as e:
                print(f"删除文件失败: {e}")
                
        except Exception as e:
            print(f"Faster-Whisper识别失败: {e}")
            print("尝试使用谷歌STT备用服务...")
            
            # 尝试谷歌STT备用服务
            try:
                text = self.google_stt_fallback(filename)
                if text:
                    print(f"谷歌STT识别结果: {text}")
                    # 进行AI翻译
                    self.translate_and_send(text)
                else:
                    print("谷歌STT也未识别到语音内容")
                    # 启动10秒定时器
                    self.start_ready_timer()
            except Exception as e2:
                print(f"谷歌STT备用服务也失败: {e2}")
                # 启动10秒定时器
                self.start_ready_timer()
            
            # 删除录音文件
            try:
                os.remove(filename)
                print(f"录音文件已删除: {filename}")
            except Exception as e3:
                print(f"删除文件失败: {e3}")
    
    def translate_and_send(self, text):
        """AI翻译并发送到VRChat"""
        try:
            print("=== 开始AI翻译 ===")
            
            # 翻译提示词
            prompt = """你是一个专业的翻译助手。请将用户输入的中文文本翻译成英文。

要求：
1. 保持原文的意思和语气
2. 翻译要自然流畅
3. 只返回翻译结果，不要添加任何解释或额外内容
4. 如果是网络用语或游戏术语，请使用对应的英文表达
5. 因为STT识别的文本可能存在错误，请进行修正并在翻译结果结尾使用[]写入修正内容

请翻译以下文本："""
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": prompt
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 1000
            }
            
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                translated_text = result['choices'][0]['message']['content'].strip()
                print(f"AI翻译结果: {translated_text}")
                
                # 拼接原文和翻译
                combined_text = f"{text}\n{translated_text}"
                
                # 发送到VRChat
                self.vrchat_client.send_message("/chatbox/input", [combined_text, True])
                print(f"已发送到VRChat: {text} -> {translated_text}")
                
                # 启动10秒定时器
                self.start_ready_timer()
                
            else:
                print(f"AI翻译失败: {response.status_code} - {response.text}")
                # 启动10秒定时器
                self.start_ready_timer()
                
        except Exception as e:
            print(f"AI翻译出错: {e}")
            # 启动10秒定时器
            self.start_ready_timer()
    
    def google_stt_fallback(self, filename):
        """谷歌STT备用服务"""
        if not GOOGLE_STT_AVAILABLE:
            print("谷歌STT服务不可用，未安装speech_recognition库")
            return None
        
        try:
            recognizer = sr.Recognizer()
            
            with sr.AudioFile(filename) as source:
                # 调整环境噪音
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                # 录制音频
                audio = recognizer.record(source)
            
            # 使用谷歌STT识别
            text = recognizer.recognize_google(audio, language='zh-CN')
            return text.strip()
            
        except sr.UnknownValueError:
            print("谷歌STT无法识别语音内容")
            return None
        except sr.RequestError as e:
            print(f"谷歌STT服务请求失败: {e}")
            return None
        except Exception as e:
            print(f"谷歌STT处理失败: {e}")
            return None
    
    def cleanup(self):
        """清理资源"""
        if self.audio:
            self.audio.terminate()
        print("\n程序已退出")
    
    def run(self):
        """运行插件"""
        try:
            # 设置键盘监听
            self.setup_keyboard_listener()
            
            # 主循环
            while True:
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n程序被用户中断")
        finally:
            self.cleanup()

def main():
    translator = VRChatVoiceTranslator()
    translator.run()

if __name__ == "__main__":
    main() 
