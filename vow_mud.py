from core.processors.movement_processor import MovementProcessor
from core.managers.logger_manager import logger_manager
from core.world import world_map
from core.processors.command_processor import command_processor
from core.processors.chat_processor import chat_processor
from core.processors.movement_processor import movement_processor
from core.server import start_server
import asyncio

async def main():
    # start processors
    asyncio.create_task(command_processor.run())
    asyncio.create_task(chat_processor.run())
    asyncio.create_task(movement_processor.run())

    # start loggers
    await logger_manager.setup_logger_authorization()
    await logger_manager.setup_logger_chat()

    # create and populate world
    await world_map.load_map_geography()

    # start the server
    await start_server()

    # shut down loggers
    await logger_manager.authorization.info({'type': 'INFO', 'message': 'Authentication logger shutdown.'})
    await logger_manager.chat.info({'type': 'INFO', 'message': 'Authentication logger shutdown.'})
    await logger_manager.authorization.shutdown()
    await logger_manager.chat.shutdown()

if __name__ == '__main__':
    asyncio.run(main())