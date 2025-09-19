import logging
import logging.handlers
import pickle
import socketserver
import struct
import random
from colorama import init, Fore, Style
import sconfig

init(autoreset=True)


class ColorFormatter(logging.Formatter):
    # 为不同应用分配的颜色族（每个颜色族包含普通和亮色版本）
    COLOR_FAMILIES = [
        (Fore.BLUE, Fore.LIGHTBLUE_EX),
        (Fore.CYAN, Fore.LIGHTCYAN_EX),
        (Fore.MAGENTA, Fore.LIGHTMAGENTA_EX),
        (Fore.GREEN, Fore.LIGHTGREEN_EX),
        (Fore.YELLOW, Fore.LIGHTYELLOW_EX),
        (Fore.RED, Fore.LIGHTRED_EX),
        (Fore.WHITE, Style.BRIGHT + Fore.WHITE),
        # 可以添加更多颜色组合
        (Style.DIM + Fore.BLUE, Fore.BLUE),
        (Style.DIM + Fore.GREEN, Fore.GREEN),
        (Style.DIM + Fore.CYAN, Fore.CYAN),
        (Style.DIM + Fore.MAGENTA, Fore.MAGENTA),
        (Style.DIM + Fore.YELLOW, Fore.YELLOW),
        (Style.DIM + Fore.RED, Fore.RED),
    ]

    # 日志级别权重（数值越大，颜色越亮）
    LEVEL_WEIGHT = {
        "DEBUG": 0,
        "INFO": 0,
        "WARNING": 1,
        "ERROR": 1,
        "CRITICAL": 1,
    }

    app_color_map = {}
    used_colors = set()  # 记录已使用的颜色
    color_index = 0  # 当前分配到的颜色索引

    def get_app_color_family(self, app_name: str):
        """为每个应用分配一个唯一的颜色族"""
        if app_name not in self.app_color_map:
            # 如果还有未使用的颜色，按顺序分配
            if self.color_index < len(self.COLOR_FAMILIES):
                color_family = self.COLOR_FAMILIES[self.color_index]
                self.app_color_map[app_name] = color_family
                self.used_colors.add(self.color_index)
                self.color_index += 1
            else:
                # 如果颜色用完了，输出警告并循环使用
                print(f"Warning: Color pool exhausted. Reusing colors for app '{app_name}'.")
                color_family = self.COLOR_FAMILIES[len(self.app_color_map) % len(self.COLOR_FAMILIES)]
                self.app_color_map[app_name] = color_family

        return self.app_color_map[app_name]

    def get_color_by_level(self, app_name: str, level: str):
        """根据应用名和日志级别返回对应的颜色"""
        color_family = self.get_app_color_family(app_name)
        weight = self.LEVEL_WEIGHT.get(level, 0)
        return color_family[weight]

    def format(self, record):
        # 根据应用名和日志级别获取颜色
        app_color = self.get_color_by_level(record.name, record.levelname)

        # 格式化原始日志
        message = super().format(record)

        # 整行使用对应颜色
        return app_color + message + Style.RESET_ALL


class LogRecordStreamHandler(socketserver.StreamRequestHandler):
    def handle(self):
        while True:
            try:
                chunk = self.connection.recv(4)
                if len(chunk) < 4:
                    break
                slen = struct.unpack(">L", chunk)[0]
                chunk = self.connection.recv(slen)
                while len(chunk) < slen:
                    chunk += self.connection.recv(slen - len(chunk))
                obj = self.unPickle(chunk)
                record = logging.makeLogRecord(obj)
                logger = logging.getLogger(record.name)
                logger.handle(record)
            except ConnectionResetError as err:
                logging.info("connection reset")
                break

    def unPickle(self, data):
        return pickle.loads(data)


class LogRecordSocketReceiver(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

    def __init__(self, host="0.0.0.0", port=sconfig.settings.LOG_PORT, handler=LogRecordStreamHandler):
        super().__init__((host, port), handler)


def run_log_server():
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # 控制台输出
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ColorFormatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    root.addHandler(console_handler)

    file_handler = logging.handlers.TimedRotatingFileHandler(
        "../logs/server.log", when="midnight", backupCount=7, encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    root.addHandler(file_handler)

    tcpserver = LogRecordSocketReceiver()
    print("🚀 Log server running on port 9020")
    tcpserver.serve_forever()


if __name__ == "__main__":
    run_log_server()
