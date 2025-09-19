import logging
import logging.handlers

logger = logging.getLogger("my-app1")
logger.setLevel(logging.DEBUG)

# 把日志直接发给本地 log server
socket_handler = logging.handlers.SocketHandler('localhost', 9020)
logger.addHandler(socket_handler)

logger.info("Hello, this goes to local logging server")
logger.error("Oops, something bad happened")