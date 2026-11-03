# Omega-7 dashboard tab

URL: https://ha.salientpoint.net/home-hub/omega7

The custom omega7-card shows the live physical ocular display, shared vox history,
text commands, microphone input, and optional queued reply audio. It talks to the
skull's existing backend; this is separate from the HA Assist conversation agent.

## Connection

`custom_components/omega7_bridge` is enabled by `omega7_bridge:` in configuration.yaml.
Its private configuration `/config/omega7_bridge.json` contains the fixed skull
URL, a dedicated web session token, and its TLS certificate SHA-256 fingerprint.
The file is mode 0600, excluded from source control, and never sent to browsers.
Changing the skull certificate requires updating the fingerprint and restarting HA.
The skull web session expires after one year unless revoked sooner.

The bridge exposes only state, ocular frames, individual audio clips, text commands,
and WAV upload through authenticated HA WebSocket calls. It requires an HA admin
because the skull conversation can request maintenance. No arbitrary URL forwarding.

The card uses HTTPS microphone access, converts audio to mono 16 kHz WAV, and caps
recording at 25 seconds. Audio playback is opt-in and may require a browser tap.
Eye snapshots update at roughly four frames per second; state every 1.2 seconds.
Leaving the tab releases microphone capture, playback, and polling. The eye pauses
when the page is hidden. A new browser view starts at the newest audio id so it
won't replay old conversations. The skull itself may also speak the reply.

## Recovery

The deployment saved the prior HA configuration under /config/omega7-backup-* and
the prior dashboard in build/before-omega7-*. Remove the Omega-7 view/resource and
configuration.yaml entry to uninstall; retain private credentials only if needed.

No automated tests or live spoken commands were run as part of this installation.
