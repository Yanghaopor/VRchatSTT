@echo off
chcp 65001 >nul
echo ========================================
echo VRChat语音翻译插件 - 启动脚本
echo ========================================
echo.

echo 正在检查配置文件...
if not exist "settings.json" (
    echo 错误：未找到settings.json配置文件
    echo 请确保配置文件存在并包含有效的API密钥
    pause
    exit /b 1
)

echo 配置文件检查通过
echo.

echo 正在启动VRChat语音翻译插件...
echo 按F4键开始/停止录音
echo 按Ctrl+C退出程序
echo.

python VRchat_videoRest.py

echo.
echo 程序已退出
pause 