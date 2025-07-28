#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Faster Whisper 测试脚本
测试 faster-whisper 的语音识别功能
"""

import os
import time
from faster_whisper import WhisperModel

def test_faster_whisper():
    """测试 Faster Whisper 语音识别"""
    print("=== Faster Whisper 语音识别测试 ===")
    
    # 检查是否有音频文件
    audio_file = "temp_vrchat_audio.wav"
    if not os.path.exists(audio_file):
        print(f"音频文件不存在: {audio_file}")
        print("请先运行VRChat插件录制一段音频")
        return
    
    print(f"音频文件: {audio_file}")
    print(f"文件大小: {os.path.getsize(audio_file) / 1024:.2f} KB")
    
    try:
        # 加载模型
        print("正在加载Faster Whisper模型...")
        start_time = time.time()
        
        # 使用CPU模式，int8量化以节省内存
        model = WhisperModel("base", device="cpu", compute_type="int8")
        
        load_time = time.time() - start_time
        print(f"模型加载完成！耗时: {load_time:.2f}秒")
        
        # 转录音频
        print("开始语音识别...")
        start_time = time.time()
        
        # 使用中文语言参数
        segments, info = model.transcribe(audio_file, language="zh")
        
        # 合并所有片段
        text = " ".join([segment.text for segment in segments]).strip()
        
        transcribe_time = time.time() - start_time
        print(f"识别完成！耗时: {transcribe_time:.2f}秒")
        print(f"识别结果: {text}")
        
        # 显示详细信息
        print(f"语言: {info.language}")
        print(f"语言概率: {info.language_probability:.2f}")
        
    except Exception as e:
        print(f"识别失败: {e}")
        print(f"错误类型: {type(e)}")

if __name__ == "__main__":
    test_faster_whisper() 