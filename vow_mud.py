from core.managers.logger_manager import logger_manager
from core.processors.command_processor import command_processor
from core.processors.chat_processor import chat_processor
from core.maps import Map
from core.server import start_server
import asyncio

async def main():
    # Start all processors
    asyncio.create_task(command_processor.run())
    asyncio.create_task(chat_processor.run())

    await logger_manager.setup_logger_authorization()
    await logger_manager.setup_logger_chat()
    
    await start_server()

    # map1 = Map('map1', '00001')
    # map1.initialize('game_modules/module1/map1.json')
    await logger_manager.authorization.info({'type': 'INFO', 'message': 'Authentication logger shutdown.'})
    await logger_manager.chat.info({'type': 'INFO', 'message': 'Authentication logger shutdown.'})
    await logger_manager.authorization.shutdown()
    await logger_manager.chat.shutdown()

if __name__ == '__main__':
    asyncio.run(main())