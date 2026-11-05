package com.evofactory.homeboard

import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import android.graphics.BitmapFactory
import android.net.Uri
import android.widget.Toast
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.produceState
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.RectangleShape
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.em
import androidx.compose.ui.unit.sp
import androidx.tv.material3.Border
import androidx.tv.material3.ClickableSurfaceDefaults
import androidx.tv.material3.Glow
import androidx.tv.material3.LocalContentColor
import androidx.tv.material3.MaterialTheme
import androidx.tv.material3.Surface
import androidx.tv.material3.Text
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.time.OffsetDateTime
import java.time.format.DateTimeParseException

/** Followed always: the Spotify player the Deco Noir dashboard's Now Playing card shows */
const val SPOTIFY_ENTITY = "media_player.spotify"

private val SpotifyPackages = listOf("com.spotify.tv.android", "com.spotify.music")

/**
 * Now Playing along the bottom, from Home Assistant's Spotify player: album art, the track in
 * Poiret One, artist and album, a progress rule, then previous / play-pause / next (sent through
 * Home Assistant, so they work wherever Spotify is playing) and a button that opens Spotify here.
 */
@Composable
fun SpotifyBar(connection: HaConnection?, server: HaServer, modifier: Modifier = Modifier) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val entity = connection?.entities?.get(SPOTIFY_ENTITY)
    val session = connection?.session
    val state = entity?.state
    val active = state == "playing" || state == "paused"
    val attributes = entity?.attributes

    fun send(service: String) {
        val live = session ?: return
        scope.launch {
            try {
                live.callService("media_player", service, SPOTIFY_ENTITY)
            } catch (e: HaException) {
                Toast.makeText(context, e.message, Toast.LENGTH_LONG).show()
            }
        }
    }

    Row(
        modifier = modifier
            .background(MaterialTheme.colorScheme.surfaceVariant)
            .decoFrame()
            .padding(horizontal = 14.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(18.dp),
    ) {
        AlbumArt(server, attributes?.string("entity_picture")?.takeIf { active })
        Column(Modifier.weight(1f)) {
            val device = attributes?.string("source")
            Text(
                listOfNotNull("◆  NOW PLAYING", "SPOTIFY", device?.uppercase()).joinToString("  ·  ") + "  ◆",
                style = MaterialTheme.typography.labelSmall.copy(letterSpacing = 0.26.em),
                color = Deco.Gold,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
            Text(
                when {
                    connection == null -> "Spotify"
                    active -> attributes?.string("media_title") ?: "Spotify"
                    else -> "Nothing playing"
                },
                style = MaterialTheme.typography.headlineSmall.marquee().copy(fontSize = 24.sp, letterSpacing = 0.04.em),
                color = Deco.Ivory,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
                modifier = Modifier.padding(top = 2.dp),
            )
            Text(
                when {
                    connection == null -> "Connect Home Assistant in Settings to see and control what's playing"
                    entity == null && connection.status == HaStatus.Connected -> "No $SPOTIFY_ENTITY in Home Assistant"
                    active -> listOfNotNull(attributes?.string("media_artist"), attributes?.string("media_album_name")).joinToString(" · ")
                    else -> "Start something in Spotify, or pick up where you left off"
                },
                style = MaterialTheme.typography.bodySmall,
                color = Deco.IvoryDim,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
            if (active && attributes != null) Progress(attributes, playing = state == "playing")
        }
        if (session != null && entity != null) {
            ControlWell("mdi:skip-previous", "Previous") { send("media_previous_track") }
            ControlWell(if (state == "playing") "mdi:pause" else "mdi:play", if (state == "playing") "Pause" else "Play", large = true) {
                send("media_play_pause")
            }
            ControlWell("mdi:skip-next", "Next") { send("media_next_track") }
        }
        DecoOutlinedButton(onClick = { context.openSpotify() }) {
            MdiIcon("mdi:spotify", size = 20.dp, color = LocalContentColor.current)
            Text("Open Spotify", modifier = Modifier.padding(start = 8.dp))
        }
    }
}

private fun org.json.JSONObject.string(key: String): String? = optString(key).takeIf { has(key) && it.isNotEmpty() && it != "null" }

/** The cover, square, in a gold hairline; a gold note when there's none */
@Composable
private fun AlbumArt(server: HaServer, picture: String?) {
    val art by produceState<ImageBitmap?>(null, picture) {
        value = null
        if (picture == null) return@produceState
        val bytes = haFetchBytes(server, picture) ?: return@produceState
        value = withContext(Dispatchers.Default) {
            BitmapFactory.decodeByteArray(bytes, 0, bytes.size)?.asImageBitmap()
        }
    }
    Box(
        modifier = Modifier
            .fillMaxHeight()
            .aspectRatio(1f)
            .background(Deco.Ink)
            .border(1.dp, Deco.Hair),
        contentAlignment = Alignment.Center,
    ) {
        val image = art
        if (image != null) {
            Image(image, contentDescription = null, contentScale = ContentScale.Crop, modifier = Modifier.fillMaxSize().padding(1.dp))
        } else {
            MdiIcon("mdi:music-note", size = 32.dp, color = Deco.Gold)
        }
    }
}

/** A gold rule filling as the track plays, with the elapsed and total time in Jost */
@Composable
private fun Progress(attributes: org.json.JSONObject, playing: Boolean) {
    val duration = attributes.optDouble("media_duration").takeUnless { it.isNaN() } ?: return
    val position = attributes.optDouble("media_position").takeUnless { it.isNaN() } ?: return
    val updatedAt = attributes.string("media_position_updated_at")?.let {
        try {
            OffsetDateTime.parse(it).toInstant().toEpochMilli()
        } catch (_: DateTimeParseException) {
            null
        }
    }
    // Home Assistant reports the position as of updatedAt; while playing it moves on from there
    val elapsed by produceState(position, position, updatedAt, playing) {
        while (true) {
            value = if (playing && updatedAt != null) {
                (position + (System.currentTimeMillis() - updatedAt) / 1000.0).coerceIn(0.0, duration)
            } else {
                position
            }
            if (!playing) break
            delay(1_000)
        }
    }
    Row(
        modifier = Modifier.fillMaxWidth().padding(top = 6.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Text(clock(elapsed), style = MaterialTheme.typography.labelSmall.figures(FontWeight.Normal), color = Deco.IvoryDim)
        Box(Modifier.weight(1f).height(3.dp).background(Deco.HairFaint)) {
            Box(Modifier.fillMaxHeight().fillMaxWidth((elapsed / duration).toFloat().coerceIn(0f, 1f)).background(Deco.Gold))
        }
        Text(clock(duration), style = MaterialTheme.typography.labelSmall.figures(FontWeight.Normal), color = Deco.IvoryDim)
    }
}

private fun clock(seconds: Double): String {
    val total = seconds.toInt()
    return "%d:%02d".format(total / 60, total % 60)
}

/** A cut-corner well with one icon, like the dashboard's scene buttons; play/pause is a size up */
@Composable
private fun ControlWell(icon: String, label: String, large: Boolean = false, onClick: () -> Unit) {
    val colors = MaterialTheme.colorScheme
    val size = if (large) 60.dp else 48.dp
    Surface(
        onClick = onClick,
        modifier = Modifier.size(size).semantics { contentDescription = label },
        shape = ClickableSurfaceDefaults.shape(DecoWellShape),
        colors = ClickableSurfaceDefaults.colors(
            containerColor = if (large) Deco.Gold.copy(alpha = 0.18f) else colors.surfaceVariant,
            contentColor = Deco.GoldHi,
            focusedContainerColor = colors.inverseSurface,
            focusedContentColor = colors.inverseOnSurface,
        ),
        border = ClickableSurfaceDefaults.border(
            border = Border(BorderStroke(1.dp, Deco.Hair), shape = DecoWellShape),
        ),
        glow = ClickableSurfaceDefaults.glow(focusedGlow = Glow(Deco.Gold.copy(alpha = 0.45f), 10.dp)),
    ) {
        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            MdiIcon(icon, size = if (large) 32.dp else 24.dp, color = LocalContentColor.current)
        }
    }
}

/** Opens the Spotify app (the TV one first), or its store page if neither is installed */
fun Context.openSpotify() {
    for (pkg in SpotifyPackages) {
        val intent = packageManager.getLeanbackLaunchIntentForPackage(pkg) ?: packageManager.getLaunchIntentForPackage(pkg)
        if (intent != null) {
            startActivity(intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
            return
        }
    }
    for (store in listOf("amzn://apps/android?p=${SpotifyPackages[0]}", "market://details?id=${SpotifyPackages[0]}")) {
        try {
            startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(store)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
            return
        } catch (_: ActivityNotFoundException) {
        }
    }
    Toast.makeText(this, "Install Spotify from your TV's app store", Toast.LENGTH_LONG).show()
}
