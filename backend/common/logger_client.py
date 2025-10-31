import logging
import logging.handlers
from backend.common import sconfig

def init(name):
    # ----------------------------
    # 1. 创建 SocketHandler
    # ----------------------------
    socket_handler = logging.handlers.SocketHandler("localhost", sconfig.settings.LOG_PORT)

    # ----------------------------
    # 2. 自定义 Filter 将所有日志改名
    # ----------------------------
    class RenameFilter(logging.Filter):
        def filter(self, record):
            record.name = name
            return True

    socket_handler.addFilter(RenameFilter())

    # ----------------------------
    # 3. 配置 root logger
    # ----------------------------
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()  # 先清理
    root_logger.addHandler(socket_handler)  # 再加

    # --- redirect logger ---
    loggers_to_configure = [
        'fastmcp',
        'uvicorn',
        'uvicorn.access',
        'uvicorn.error',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.websockets',
        'websockets',
        'websockets.legacy',
        'websockets.server',
        'asyncio',
        'multipart',
        'httptools',
        'h11'
    ]

    for logger_name in loggers_to_configure:
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.addHandler(socket_handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False

    # ----------------------------
    # 4. 测试
    # ----------------------------
    logging.info(f"Logging for {name} initialized")
