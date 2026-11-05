"""Constants for the go2rtc Media Player integration."""

DOMAIN = "go2rtc_media_player"

CONF_STREAM = "stream"
CONF_AUDIO = "audio"
CONF_URL = "url"

DEFAULT_URL = "http://127.0.0.1:1984"
DEFAULT_AUDIO = "pcma"

# Common audio codecs accepted by cameras with two-way audio / backchannel
AUDIO_OPTIONS = [
    "pcma",
    "pcmu",
    "pcma/8000",
    "pcmu/8000",
    "opus",
]
