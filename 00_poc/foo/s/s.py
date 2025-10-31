import logging
import sys
import os
from fastmcp import FastMCP


# Method 1A: Aggressive logging redirect - completely suppress console
def setup_complete_redirect():
    """Completely redirect all logging away from console"""

    # Create custom formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Create file handler
    file_handler = logging.FileHandler('../mcp_server.log')
    file_handler.setFormatter(formatter)

    # Configure root logger first
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.setLevel(logging.INFO)

    # More comprehensive list of loggers to redirect
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
        logger.addHandler(file_handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False


# Method 1B: Nuclear option - redirect stdout/stderr
class LogRedirector:
    """Redirect stdout/stderr to file"""

    def __init__(self, filename):
        self.filename = filename

    def __enter__(self):
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.log_file = open(self.filename, 'a')
        sys.stdout = self.log_file
        sys.stderr = self.log_file
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        self.log_file.close()


# Method 1C: Most effective - configure uvicorn logging specifically
def setup_uvicorn_logging_override():
    """Override uvicorn logging configuration specifically"""

    # Create file handler
    file_handler = logging.FileHandler('../mcp_server.log')
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.setLevel(logging.INFO)

    # Specifically target uvicorn access logger (this is the culprit)
    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.handlers.clear()
    uvicorn_access.addHandler(file_handler)
    uvicorn_access.propagate = False

    # Target uvicorn main logger
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.handlers.clear()
    uvicorn_logger.addHandler(file_handler)
    uvicorn_logger.propagate = False

    # Disable console output for all loggers
    for name in logging.Logger.manager.loggerDict:
        logger = logging.getLogger(name)
        logger.handlers = [h for h in logger.handlers if not isinstance(h, logging.StreamHandler)]
        if not logger.handlers:
            logger.addHandler(file_handler)
            logger.propagate = False


# Method 1D: Override using environment variable approach
def setup_env_based_logging():
    """Set uvicorn log config via environment variables"""

    # Disable uvicorn access logs entirely
    os.environ['UVICORN_ACCESS_LOG'] = 'false'

    # Create our custom handler
    file_handler = logging.FileHandler('../mcp_server.log')
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)

    # Configure all logging
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.setLevel(logging.INFO)


# Method 2: Custom logging class for more control
class CustomLogHandler(logging.Handler):
    """Custom log handler that can process and redirect logs"""

    def emit(self, record):
        # Process the log record here
        log_entry = self.format(record)

        # You can redirect to file, database, external service, etc.
        with open('custom_mcp.log', 'a') as f:
            f.write(log_entry + '\n')

        # Or send to external logging service
        # send_to_external_service(log_entry)


def setup_custom_handler_logging():
    """Setup logging with custom handler"""

    # Create and configure custom handler
    custom_handler = CustomLogHandler()
    custom_handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    ))

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(custom_handler)
    root_logger.setLevel(logging.INFO)


# Method 3: Disable specific noisy loggers
def suppress_noisy_loggers():
    """Suppress or reduce log level for noisy components"""

    # Suppress websockets deprecation warnings
    logging.getLogger('websockets.legacy').setLevel(logging.ERROR)
    logging.getLogger('websockets.server').setLevel(logging.ERROR)

    # Reduce uvicorn access logs
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)

    # Keep FastMCP logs but redirect them
    fastmcp_logger = logging.getLogger('fastmcp')
    fastmcp_logger.handlers.clear()

    # Add your custom handler to FastMCP logger
    handler = logging.FileHandler('fastmcp_only.log')
    handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    fastmcp_logger.addHandler(handler)


# Your MCP server code
mcp = FastMCP("MyServer")


@mcp.tool
def guess(x: int) -> str:
    if x == 0:  # Fix the division by zero error
        return "Cannot divide by zero"
    return str(int(x / (x - 1)))


if __name__ == "__main__":
    # Choose one of the methods below - try them in this order:

    # Option 1A: Most aggressive - redirect everything
    setup_complete_redirect()

    # Option 1B: Nuclear option - redirect stdout/stderr (uncomment if needed)
    #with LogRedirector('mcp_server.log'):
    #    mcp.run(transport="http", host="127.0.0.1", port=9000)

    # Option 1C: Target uvicorn specifically (try this if 1A doesn't work)
    #setup_uvicorn_logging_override()

    # Option 1D: Environment-based approach
    #setup_env_based_logging()

    # Run the MCP server - for options 1A, 1C, 1D
    mcp.run(
        transport="http",
        host="127.0.0.1",
        port=9000,
        # These parameters might help suppress uvicorn logs
        #log_config=None,  # Disable uvicorn's default logging config
        #access_log=False  # Disable access logging
    )

# Method 4: Environment-based logging configuration
# You can also set logging configuration via environment variables or config files

# Example using dictConfig for more sophisticated setup
import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'detailed': {
            'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s'
        }
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.FileHandler',
            'filename': 'mcp_server.log',
            'mode': 'a',
        },
        'console': {
            'level': 'ERROR',  # Only show errors on console
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout'
        }
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['default', 'console'],
            'level': 'INFO',
            'propagate': False
        },
        'fastmcp': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': False
        },
        'uvicorn': {
            'handlers': ['default'],
            'level': 'WARNING',  # Reduce uvicorn verbosity
            'propagate': False
        },
        'websockets': {
            'handlers': [],  # Suppress websockets logs
            'level': 'ERROR',
            'propagate': False
        }
    }
}


def setup_dict_config_logging():
    """Setup logging using dictConfig"""
    logging.config.dictConfig(LOGGING_CONFIG)