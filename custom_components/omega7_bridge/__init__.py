"""Authenticated, fixed-endpoint bridge to the household Servoskull."""
import asyncio
import base64
import json
import aiohttp
import probatio as vol
from homeassistant.components import websocket_api
from homeassistant.helpers.aiohttp_client import async_get_clientsession

DOMAIN = "omega7_bridge"
CONFIG_SCHEMA = vol.Schema({vol.Optional(DOMAIN): vol.Any(dict, None)}, extra=vol.ALLOW_EXTRA)

async def async_setup(hass, config):
    def read_config():
        with open(hass.config.path("omega7_bridge.json"), encoding="utf-8") as f:
            return json.load(f)
    settings = await hass.async_add_executor_job(read_config)
    hass.data[DOMAIN] = settings
    websocket_api.async_register_command(hass, request)
    return True

@websocket_api.websocket_command({
    vol.Required("type"): "omega7_bridge/request",
    vol.Required("action"): vol.In(["state", "eye", "audio", "text", "microphone"]),
    vol.Optional("audio_id"): vol.All(int, vol.Range(min=0)),
    vol.Optional("text"): vol.All(str, vol.Length(min=1, max=2000)),
    vol.Optional("wav"): vol.All(str, vol.Length(max=4000000)),
})
@websocket_api.async_response
async def request(hass, connection, msg):
    # The skull can perform maintenance through conversation, so require HA admin.
    if not connection.user.is_admin:
        connection.send_error(msg["id"], "unauthorized", "Omega-7 is available to HA administrators.")
        return
    settings = hass.data[DOMAIN]
    action = msg["action"]
    method = "GET"
    kwargs = {}
    if action == "state":
        path = "/api/state"
    elif action == "eye":
        path = "/api/ocular_frame.jpg"
    elif action == "audio":
        if "audio_id" not in msg:
            connection.send_error(msg["id"], "invalid_format", "Audio id required")
            return
        path = "/api/last_speech.wav?id=" + str(msg["audio_id"])
    elif action == "text":
        if not msg.get("text", "").strip():
            connection.send_error(msg["id"], "invalid_format", "Message required")
            return
        method, path = "POST", "/api/command"
        kwargs["json"] = {"command": msg["text"].strip()}
    else:
        try:
            wav = base64.b64decode(msg.get("wav", ""), validate=True)
            if len(wav) < 44 or wav[:4] != b"RIFF" or wav[8:12] != b"WAVE":
                raise ValueError()
        except ValueError:
            connection.send_error(msg["id"], "invalid_format", "Valid WAV audio required")
            return
        method, path = "POST", "/api/upload_audio"
        kwargs["data"] = wav
    try:
        session = async_get_clientsession(hass)
        async with session.request(method, settings["url"] + path,
                headers={"Authorization": "Bearer " + settings["token"]},
                ssl=aiohttp.Fingerprint(bytes.fromhex(settings["fingerprint"])),
                timeout=aiohttp.ClientTimeout(total=20), allow_redirects=False, **kwargs) as response:
            if response.status != 200:
                connection.send_error(msg["id"], "skull_error", "Omega-7 returned HTTP " + str(response.status))
                return
            if action in ("eye", "audio"):
                payload = await response.read()
                result = {"data": base64.b64encode(payload).decode("ascii")}
            else:
                result = await response.json()
                if action == "state":
                    result = {key: result.get(key) for key in (
                        "skull_name", "display", "temperature", "mood", "silent_mode", "vox_logs", "audio_ids")}
        connection.send_result(msg["id"], result)
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError):
        connection.send_error(msg["id"], "unavailable", "Cannot reach Omega-7 securely. A submitted command may have arrived; check the vox channel before retrying.")
