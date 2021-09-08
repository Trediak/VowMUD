from aiologger.formatters.json import FUNCTION_NAME_FIELDNAME, LOG_LEVEL_FIELDNAME
from aiologger.loggers.json import JsonLogger, ExtendedJsonFormatter
from aiologger.handlers.files import AsyncFileHandler

class LoggerManager:
    """Class which manages loggers"""
    def __init__(self):
        self.authorization = None

    async def setup_logger_authorization(self) -> None:
        # create handler to stream to log file
        self.authorization = JsonLogger()

        handler = AsyncFileHandler(filename='logs/authentication.log')
        handler.formatter = ExtendedJsonFormatter(exclude_fields=[FUNCTION_NAME_FIELDNAME, LOG_LEVEL_FIELDNAME, 'file_path', 'line_number'])
        self.authorization.add_handler(handler)

        # log that logger has started
        self.authorization.info({'type': 'INFO', 'message': 'Authentication logger started.'})

logger_manager = LoggerManager()
