#!/usr/bin/env python3
"""
AI Framework Server Runner

A robust script to start, monitor, and manage the AI Framework server.
"""

import asyncio
import logging
import signal
import sys

import aiohttp
from server import AIFrameworkServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('server.log')
    ]
)
logger = logging.getLogger(__name__)

class ServerManager:
    """Manages the AI Framework server process."""

    # Constants to replace magic numbers
    HEALTHY_STATUS_CODE = 200
    HEALTH_CHECK_TIMEOUT = 5
    HEALTH_CHECK_INTERVAL = 30  # seconds
    ERROR_RETRY_INTERVAL = 10  # seconds

    def __init__(self):
        self.server_process = None
        self.shutdown_event = asyncio.Event()
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            self.shutdown_event.set()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def start_server(self):
        """Start the AI Framework server."""
        try:
            logger.info("🚀 Starting AI Framework Server...")

            # Start server
            server = AIFrameworkServer(host="0.0.0.0", port=8001, debug=False)

            # Start server
            await server.start()

        except Exception as e:
            logger.error(f"❌ Server startup failed: {str(e)}")
            return False

        return True

    async def monitor_server(self):
        """Monitor server health and restart if needed."""
        while not self.shutdown_event.is_set():
            try:
                # Check server health
                async with aiohttp.ClientSession() as session, session.get('http://localhost:8001/health', timeout=self.HEALTH_CHECK_TIMEOUT) as response:
                    if response.status == self.HEALTHY_STATUS_CODE:
                        data = await response.json()
                        logger.info(f"✅ Server healthy: {data}")
                    else:
                        logger.warning(f"⚠️ Server unhealthy: {response.status}")

                await asyncio.sleep(self.HEALTH_CHECK_INTERVAL)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"❌ Health check failed: {str(e)}")
                await asyncio.sleep(self.ERROR_RETRY_INTERVAL)

    async def run(self):
        """Run the server manager."""
        try:
            # Start server
            server_task = asyncio.create_task(self.start_server())

            # Start monitoring
            monitor_task = asyncio.create_task(self.monitor_server())

            # Wait for shutdown
            await self.shutdown_event.wait()

            # Cleanup
            if not server_task.done():
                server_task.cancel()

            if not monitor_task.done():
                monitor_task.cancel()

            logger.info("✅ Server manager shutdown complete")

        except Exception as e:
            logger.error(f"❌ Server manager failed: {str(e)}")
            return False

        return True

def main():
    """Main entry point."""
    manager = ServerManager()

    try:
        asyncio.run(manager.run())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
