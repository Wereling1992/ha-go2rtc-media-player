"""Media player platform for go2rtc Media Player."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components import media_source
from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
    async_process_play_media_url,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_AUDIO, CONF_STREAM, CONF_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)

# go2rtc does not notify when a file finishes playing.
# Auto-return to idle after this many seconds (covers typical TTS / chimes).
_DEFAULT_PLAY_TIMEOUT = 60


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the media player from a config entry."""
    async_add_entities([Go2rtcMediaPlayer(hass, entry)])


class Go2rtcMediaPlayer(MediaPlayerEntity):
    """Representation of a go2rtc stream as a media player.

    Plays any audio (TTS, Chime TTS, music, etc.) through the camera
    speaker using go2rtc's backchannel / stream-to-camera feature.

    Volume is not controlled here — adjust it in the camera's own app
    (e.g. Tapo app). go2rtc has no volume API for stream-to-camera.
    """

    _attr_supported_features = (
        MediaPlayerEntityFeature.PLAY_MEDIA
        | MediaPlayerEntityFeature.STOP
        | MediaPlayerEntityFeature.BROWSE_MEDIA
    )
    _attr_has_entity_name = False
    _attr_device_class = MediaPlayerDeviceClass.SPEAKER
    _attr_icon = "mdi:speaker"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the media player."""
        self.hass = hass
        self._entry = entry
        data = entry.data

        self._stream: str = data[CONF_STREAM]
        self._audio: str = data[CONF_AUDIO]
        self._url: str = data[CONF_URL].rstrip("/")
        self._attr_name = data[CONF_NAME]
        self._attr_unique_id = entry.entry_id
        self._attr_state = MediaPlayerState.IDLE
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": data[CONF_NAME],
            "manufacturer": "go2rtc",
            "model": "Media Player",
        }
        self._idle_handle = None

    def _cancel_idle_timer(self) -> None:
        """Cancel any pending auto-idle timer."""
        if self._idle_handle is not None:
            self._idle_handle.cancel()
            self._idle_handle = None

    def _schedule_idle(self, delay: float) -> None:
        """Schedule return to idle after delay."""

        def _set_idle(_now=None) -> None:
            self._idle_handle = None
            if self._attr_state == MediaPlayerState.PLAYING:
                self._attr_state = MediaPlayerState.IDLE
                self.async_write_ha_state()

        self._cancel_idle_timer()
        self._idle_handle = self.hass.loop.call_later(delay, _set_idle)

    async def async_play_media(
        self, media_type: MediaType | str, media_id: str, **kwargs: Any
    ) -> None:
        """Play media on the camera speaker via go2rtc."""
        # Resolve media_source IDs (e.g. from media browser)
        if media_source.is_media_source_id(media_id):
            sourced = await media_source.async_resolve_media(
                self.hass, media_id, self.entity_id
            )
            media_id = sourced.url

        # Convert relative URLs (TTS /api/tts_proxy/...) to absolute URLs
        media_id = async_process_play_media_url(self.hass, media_id)

        # Always force file mode so ffmpeg transcodes the whole file in realtime
        extra = "#input=file"
        if isinstance(media_type, str) and media_type.startswith("#"):
            extra = media_type

        src = f"ffmpeg:{media_id}#audio={self._audio}{extra}"
        api = f"{self._url}/api/streams"

        _LOGGER.debug("Playing to stream=%s src=%s", self._stream, src)

        self._cancel_idle_timer()

        try:
            session = async_get_clientsession(self.hass)
            async with session.post(
                api,
                params={"dst": self._stream, "src": src},
                timeout=15,
            ) as resp:
                if resp.status >= 400:
                    text = await resp.text()
                    _LOGGER.error(
                        "go2rtc returned %s for stream %s: %s",
                        resp.status,
                        self._stream,
                        text,
                    )
                    self._attr_state = MediaPlayerState.IDLE
                else:
                    self._attr_state = MediaPlayerState.PLAYING
                    # go2rtc never reports end-of-file — auto-idle after timeout
                    self._schedule_idle(_DEFAULT_PLAY_TIMEOUT)
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("Failed to play media on %s: %s", self._stream, err)
            self._attr_state = MediaPlayerState.IDLE

        self.async_write_ha_state()

    async def async_media_stop(self) -> None:
        """Stop playback by clearing the source on the stream."""
        self._cancel_idle_timer()
        api = f"{self._url}/api/streams"
        try:
            session = async_get_clientsession(self.hass)
            async with session.post(
                api,
                params={"dst": self._stream, "src": ""},
                timeout=10,
            ) as resp:
                if resp.status >= 400:
                    _LOGGER.debug("Stop returned %s (often normal)", resp.status)
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Stop failed (often harmless): %s", err)

        self._attr_state = MediaPlayerState.IDLE
        self.async_write_ha_state()

    async def async_browse_media(
        self,
        media_content_type: str | None = None,
        media_content_id: str | None = None,
    ):
        """Browse media (required by some media browsers / TTS)."""
        return await media_source.async_browse_media(
            self.hass,
            media_content_id,
            content_filter=lambda item: item.media_content_type.startswith("audio/")
            or item.media_content_type
            in (MediaType.MUSIC, MediaType.AUDIO, "music", "audio"),
        )

    async def async_will_remove_from_hass(self) -> None:
        """Cancel background timers when entity is removed."""
        self._cancel_idle_timer()
