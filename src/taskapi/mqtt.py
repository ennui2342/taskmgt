import asyncio
import logging
import os

logger = logging.getLogger(__name__)


def _mqtt_host() -> str:
    return os.environ.get("MQTT_HOST", "")


def _mqtt_port() -> int:
    return int(os.environ.get("MQTT_PORT", "1883"))


async def _do_publish(topic: str, payload: str) -> None:
    try:
        import aiomqtt
        async with aiomqtt.Client(hostname=_mqtt_host(), port=_mqtt_port()) as client:
            await client.publish(topic, payload)
    except Exception as e:
        logger.warning("MQTT publish failed: %s", e)


def mqtt_publish(topic: str, payload: str) -> None:
    """Fire-and-forget MQTT publish. Silently skips if MQTT_HOST is not set."""
    if not _mqtt_host():
        return
    asyncio.create_task(_do_publish(topic, payload))
