from core.logger_manager import logger_manager
from core.maps import Map
from core.server import start_server
import asyncio

async def main():
    await logger_manager.setup_logger_authorization()
    await start_server()

    # map1 = Map('map1', '00001')
    # map1.initialize('game_modules/module1/map1.json')
    await logger_manager.authorization.info({'type': 'INFO', 'message': 'Authentication logger shutdown.'})
    await logger_manager.authorization.shutdown()

if __name__ == '__main__':
    asyncio.run(main())