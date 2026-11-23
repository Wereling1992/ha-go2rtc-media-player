# go2rtc Media Player

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/Wereling1992/ha-go2rtc-media-player.svg)](https://github.com/Wereling1992/ha-go2rtc-media-player/releases)
[![License](https://img.shields.io/github/license/Wereling1992/ha-go2rtc-media-player.svg)](LICENSE)

Turn any go2rtc camera stream with two-way audio into a Home Assistant `media_player`.

Play TTS, Chime TTS, music, or any audio file through the camera speaker. Configured entirely from the UI.

## Features

- Add and manage players from the UI (Config Flow + Options Flow)
- Works with `media_player.play_media`, TTS, Chime TTS, Music Assistant, etc.
- Uses the official go2rtc [Stream to camera](https://go2rtc.org/internal/streams/#stream-to-camera) API
- Change name, stream, or codec later without restarting Home Assistant
- Compatible with the same backchannel mechanism used by [AlexxIT/WebRTC](https://github.com/AlexxIT/WebRTC)

## Requirements

1. [go2rtc](https://github.com/AlexxIT/go2rtc) is running and reachable
2. Your camera stream is already defined in go2rtc **and supports two-way audio**
3. You know the audio codec the camera expects on the backchannel

### Supported cameras (examples)

| Brand / Protocol              | Typical codec          |
|-------------------------------|------------------------|
| Tapo (`tapo://`)              | `pcma`                 |
| Reolink                       | `pcmu/8000` or `pcma`  |
| Dahua / Amcrest               | `pcma` or `pcma/48000` |
| Hikvision (ISAPI)             | `pcma`                 |
| Generic RTSP with backchannel | Check go2rtc probe     |

> **Important for Tapo**  
> The stream **must** include a `tapo://` source. Pure RTSP does **not** expose the backchannel on Tapo cameras.

## Installation

### HACS (Recommended)

1. Open **HACS** → **Integrations**
2. Click the three dots (⋮) → **Custom repositories**
3. Add the following repository and select category **Integration**:
   ```
   https://github.com/Wereling1992/ha-go2rtc-media-player
   ```
4. Search for **go2rtc Media Player** and download it
5. Restart Home Assistant

### Manual Installation

1. Download the latest [Release](https://github.com/Wereling1992/ha-go2rtc-media-player/releases)
2. Copy the `custom_components/go2rtc_media_player` folder into your Home Assistant `config/custom_components/` directory
3. Restart Home Assistant

## Configuration

1. Go to **Settings → Devices & Services**
2. Click **+ Add Integration**
3. Search for **go2rtc Media Player**
4. Fill in the form:

| Field               | Example                  | Description                              |
|---------------------|--------------------------|------------------------------------------|
| Name                | Front Door Speaker       | Friendly name                            |
| go2rtc stream name  | front_door               | Must match the name in go2rtc            |
| Audio codec         | pcma                     | Codec the camera accepts                 |
| go2rtc base URL     | http://127.0.0.1:1984    | Change only if go2rtc is remote          |

You will get a new entity, e.g. `media_player.front_door_speaker`.

To edit later, open the integration and use the **gear (options)** icon.

## Usage

### Chime TTS

```yaml
service: chime_tts.say
data:
  message: "Someone is at the door"
  chime_path: "toast"
target:
  entity_id: media_player.front_door_speaker
```

### Standard TTS

```yaml
service: tts.speak
target:
  entity_id: media_player.front_door_speaker
data:
  media_player_entity_id: media_player.front_door_speaker
  message: "Hello from the camera"
```

### Play a file

```yaml
service: media_player.play_media
target:
  entity_id: media_player.front_door_speaker
data:
  media_content_id: "https://example.com/sound.mp3"
  media_content_type: music
```

## Troubleshooting

1. Open the go2rtc Web UI → select your stream → **Info / Probe**
2. Confirm you see a line similar to:
   ```
   audio, sendonly, PCMA/8000
   ```
3. Test **Play Audio** directly from the go2rtc Web UI first
4. If the Web UI works but the media_player does not, check the Home Assistant log for `go2rtc_media_player`

## FAQ

### Why is there no volume control in Home Assistant?

go2rtc's stream-to-camera API has no volume parameter.  
Software volume filters via ffmpeg often break audio on cameras (especially Tapo).

Adjust the speaker volume in the camera's own app instead:

- **Tapo**: Tapo app → camera settings → sound / speaker volume
- Other brands: manufacturer app or camera web UI

Chime TTS also has its own volume / gain options if you need louder or quieter announcements.

### Why does the player stay on "Playing"?

go2rtc does not report when a file has finished playing.  
This integration therefore:

- Sets state to **Playing** when the API call succeeds
- Automatically returns to **Idle** after about 60 seconds
- Returns to **Idle** immediately if you call `media_player.media_stop`

Short TTS clips often finish well before the 60-second timeout; the state is only a rough indicator.

### Tapo camera has no sound

1. The go2rtc stream **must** include a `tapo://` source (not only `rtsp://`)
2. Confirm probe shows `audio, sendonly, PCMA/8000`
3. Use audio codec `pcma`
4. Enable **Third-Party Compatibility** in the Tapo app (Lab section) if needed

## Credits

Inspired by the media_player platform in [AlexxIT/WebRTC](https://github.com/AlexxIT/WebRTC).  
Uses the public go2rtc Stream-to-camera API.

## License

MIT
