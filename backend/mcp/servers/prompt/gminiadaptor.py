from google.genai import types
from google import genai

import threading
import time
from typing import Any, Optional
from collections import deque

class GaminiAdaptor:

    _instance: Optional['GaminiAdaptor'] = None
    _lock = threading.Lock()

    def __new__(cls) -> 'GaminiAdaptor':
        """线程安全的单例实现"""
        if cls._instance is None:
            with cls._lock:
                # 双重检查锁定模式
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化（只会执行一次）"""
        # 防止重复初始化
        if hasattr(self, '_initialized'):
            return

        # 速率限制相关
        self._max_calls_per_minute = 10
        self._time_window = 60  # 60秒窗口
        self._call_times = deque()  # 存储调用时间戳
        self._rate_limit_lock = threading.Lock()  # 速率限制专用锁

        # Initialize your adaptor here
        self.google_client = genai.Client(api_key="AIzaSyAf8NARQmskJOPz4QJtGBNZbE1lS3H-CV8")

    def _wait_for_rate_limit(self) -> None:
        """
        检查速率限制并等待直到可以执行
        使用滑动窗口算法
        """
        with self._rate_limit_lock:
            current_time = time.time()

            # 移除超过时间窗口的旧记录
            while self._call_times and current_time - self._call_times[0] >= self._time_window:
                self._call_times.popleft()

            # 如果当前调用次数已达上限，需要等待
            while len(self._call_times) >= self._max_calls_per_minute:
                # 计算需要等待的时间
                oldest_call = self._call_times[0]
                wait_time = self._time_window - (current_time - oldest_call)

                if wait_time > 0:
                    print(f"速率限制：已达到每分钟{self._max_calls_per_minute}次调用上限，等待 {wait_time:.2f} 秒...")
                    # 释放锁进行等待，避免阻塞其他线程
                    self._rate_limit_lock.release()
                    try:
                        time.sleep(wait_time + 0.1)  # 多等待0.1秒确保时间窗口过期
                    finally:
                        self._rate_limit_lock.acquire()

                # 重新获取当前时间并清理过期记录
                current_time = time.time()
                while self._call_times and current_time - self._call_times[0] >= self._time_window:
                    self._call_times.popleft()

            # 记录本次调用时间
            self._call_times.append(current_time)

    def generate(self, prompt, level="low"):

        self._wait_for_rate_limit()

        if level == "low":
            response = self.google_client.models.generate_content(
                model="gemma-3-27b-it",
                contents=prompt
            )
        else:
            try:
                response = self.google_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        thinking_config=types.ThinkingConfig(thinking_budget=-1)
                    ),
                )
            except:
                response = self.google_client.models.generate_content(
                    model="gemma-3-27b-it",
                    contents=prompt
                )
        return response.text

if __name__ == "__main__":
    llm = GaminiAdaptor()
    r = llm.generate("hello")
    print(r)