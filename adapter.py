import asyncio
import os
import logging
from typing import Optional

from nicotin import Client
from gateway.platforms.base import (
    BasePlatformAdapter,
    MessageEvent,
    MessageType,
    SendResult,
)

logger = logging.getLogger(__name__)


class RubikaAdapter(BasePlatformAdapter):
    """Rubika messaging adapter using NICOTIN library."""

    def __init__(self, config):
        super().__init__(config, "rubika")
        extra = config.extra or {}
        self._bot_token = (
            extra.get("bot_token")
            or os.getenv("RUBIKA_BOT_TOKEN", "")
        )
        self._client: Optional[Client] = None
        self._running = False
        self._connected = False

        if not self._bot_token:
            logger.error("RUBIKA_BOT_TOKEN is not set")

    async def connect(self, *, is_reconnect: bool = False) -> bool:
        """Connect to Rubika using the bot token."""
        if not self._bot_token:
            logger.error("Cannot connect: no bot token")
            return False

        try:
            self._client = Client(bot_token=self._bot_token)
            self._running = True

            # Register message handler using NICOTIN's decorator style
            @self._client.on_message()
            async def handle_message(client, message):
                if not self._running:
                    return
                try:
                    text = message.text or ""
                    chat_id = str(message.chat.id)
                    user_id = (
                        str(message.from_user.id)
                        if message.from_user
                        else ""
                    )
                    user_name = (
                        message.from_user.first_name
                        if message.from_user
                        else "Rubika User"
                    )

                    source = self.build_source(
                        chat_id=chat_id,
                        chat_name=user_name,
                        chat_type="dm",
                        user_id=user_id,
                        user_name=user_name,
                    )

                    event = MessageEvent(
                        text=text,
                        message_type=MessageType.TEXT,
                        source=source,
                        message_id=str(getattr(message, "id", "")),
                    )

                    await self.handle_message(event)
                except Exception as e:
                    logger.error(
                        f"Error handling Rubika message: {e}",
                        exc_info=True,
                    )

            # Run NICOTIN client in a background thread
            asyncio.create_task(self._run_client())

            # Give it a moment to establish the connection
            await asyncio.sleep(2)

            self._connected = True
            self._mark_connected()
            logger.info("Rubika adapter connected")
            return True

        except Exception as e:
            logger.error(f"Failed to connect Rubika: {e}", exc_info=True)
            return False

    async def _run_client(self):
        """Run NICOTIN client in a separate thread."""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._client.run)
        except Exception as e:
            logger.error(f"Rubika client error: {e}", exc_info=True)
            self._running = False
            self._connected = False

    async def disconnect(self) -> None:
        """Disconnect from Rubika."""
        self._running = False
        self._connected = False
        self._mark_disconnected()
        logger.info("Rubika adapter disconnected")

    async def send(self, chat_id: str, content: str, **kwargs) -> SendResult:
        """Send a message to Rubika."""
        if not self._client or not self._running or not self._connected:
            return SendResult(
                success=False,
                error="Rubika client not connected",
            )

        try:
            result = await self._client.send_message(
                chat_id=chat_id,
                text=content,
            )
            message_id = getattr(result, "id", None)
            return SendResult(
                success=True,
                message_id=str(message_id) if message_id else None,
            )
        except Exception as e:
            logger.error(
                f"Failed to send Rubika message: {e}",
                exc_info=True,
            )
            return SendResult(success=False, error=str(e))

    async def get_chat_info(self, chat_id: str) -> dict:
        """Return basic chat info."""
        return {"name": chat_id, "type": "dm", "chat_id": chat_id}
