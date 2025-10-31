@echo off
setlocal

rem 设置一个独特的窗口标题，用于稍后查找
title My_Batch_Script_12345

echo 正在启动子进程...

start "子进程1" notepad.exe
start "子进程2" calc.exe

echo 子进程已启动。脚本的PID将被查找。
pause

echo 正在终止子进程...

rem 获取当前脚本的PID，通过窗口标题查找
for /f "tokens=2" %%i in ('tasklist /nh /fi "imagename eq cmd.exe" /fi "windowtitle eq My_Batch_Script_12345"') do set BAT_PID=%%i

echo 找到的脚本PID：%BAT_PID%

rem 使用 PID 终止子进程
if defined BAT_PID (
    for /f "tokens=2" %%a in ('wmic process where "ParentProcessID=%BAT_PID%" get ProcessID 2^>NUL ^| findstr /r "[0-9]"') do (
        echo 正在终止进程PID: %%a
        taskkill /f /pid %%a
    )
) else (
    echo 警告：未找到脚本的PID，无法终止子进程。
)

echo 子进程终止完成。
endlocal
exit