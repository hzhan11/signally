import concurrent.futures
import subprocess
import os
import signal
import sys


def run_script(script_path, cwd):
    """一个在子进程中运行指定脚本的函数。"""
    print(f"Starting script {script_path} in directory {cwd}...")
    try:
        # 使用 subprocess.run，它会等待命令完成并返回结果
        result = subprocess.run(
            ['python', script_path],
            cwd=cwd,
            check=True,  # 如果命令返回非零退出码，则抛出异常
            capture_output=True,  # 捕获 stdout 和 stderr
            text=True  # 将输出解码为文本
        )
        print(f"--- Output for {script_path} ---")
        print(result.stdout)
        print(f"--- Finished {script_path} ---")
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running script {script_path}: {e}")
        print(e.stderr)
        return None


def signal_handler(signum, frame):
    """信号处理函数，用于优雅退出。"""
    print(f"\n接收到信号 {signum}，正在终止所有子进程...")
    # 当接收到信号时，sys.exit() 会触发 with 块的退出逻辑
    sys.exit(1)


if __name__ == "__main__":
    # 定义任务列表 (假设您已定义好 tasks 变量)
    from pathlib import Path

    script_dir = Path(__file__).parent.absolute()

    tasks = [
        ('db_main.py', str(script_dir / 'db')),
        ('api_main.py', str(script_dir / 'api')),
        ('infocollector.py', str(script_dir / 'mcp/servers')),
        ('signalpredictor.py', str(script_dir / 'mcp/servers')),
        ('trader.py',str(script_dir / 'mcp/servers')),
        ('orchestrate.py', str(script_dir / 'mcp')),
    ]

    # 设置信号处理函数
    signal.signal(signal.SIGINT, signal_handler)  # 处理 Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # 处理 kill 命令

    print("主程序开始运行。按下 Ctrl+C 或使用 kill 命令来终止。")

    # 使用 with 语句来确保进程池被妥善关闭
    try:
        with concurrent.futures.ProcessPoolExecutor() as executor:
            # 提交任务
            future_to_task = {executor.submit(run_script, task[0], task[1]): task for task in tasks}

            # 等待所有任务完成
            for future in concurrent.futures.as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    # 获取结果，这里我们没有返回值，所以只检查异常
                    future.result()
                except Exception as exc:
                    print(f'{task[0]} generated an exception: {exc}')

    except SystemExit:
        # 捕获 signal_handler 中引发的 SystemExit
        print("主程序已通过信号处理退出。")

    print("程序已结束。所有子进程已终止。")