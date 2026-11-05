package com.evofactory.homeboard

import android.widget.Toast
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalSoftwareKeyboardController
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.em
import androidx.compose.ui.unit.sp
import androidx.tv.material3.MaterialTheme
import androidx.tv.material3.Text
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.sin

// Often enough that a reply follows soon after it's spoken
private const val STATE_POLL_MS = 1_500L
private const val DEFAULT_OMEGA7_ADDRESS = "192.168.0.108"
private const val RETRY_MS = 10_000L

/** What a press on a preset says to Omega-7 */
private val PresetCommands = listOf(
    "Status report" to "mdi:console",
    "What's on today?" to "mdi:calendar-clock",
    "Tell me something about the Imperium" to "mdi:skull",
)

/**
 * The Omega-7 page: its eye, live, in a gold ring with its name and mood; the vox log; the
 * cogitator's vitals; and buttons to wake it, send presets, type a command or run a screensaver.
 */
@Composable
fun Omega7Page(
    server: Omega7Server,
    voiceOn: Boolean,
    onVoiceChange: (Boolean) -> Unit,
    onSetUp: () -> Unit,
    onLoginRejected: () -> Unit,
    modifier: Modifier = Modifier,
) {
    if (!server.isSet) {
        Box(modifier, contentAlignment = Alignment.Center) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                MdiIcon("mdi:skull", size = 64.dp, color = Deco.Gold)
                Text("OMEGA-7", style = MaterialTheme.typography.displaySmall.marquee(), color = Deco.GoldHi, modifier = Modifier.padding(top = 12.dp))
                Text(
                    "Connect the TV to the servo-skull's web remote. Say \"Omega-7, show the web access code\" and enter it here.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = Deco.IvoryDim,
                    textAlign = TextAlign.Center,
                    modifier = Modifier.padding(vertical = 16.dp).fillMaxWidth(0.6f),
                )
                DecoButton(onClick = onSetUp) { Text("Connect Omega-7") }
            }
        }
        return
    }
    val client = remember(server) { Omega7Client(server) }
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var state by remember { mutableStateOf<Omega7State?>(null) }
    var problem by remember { mutableStateOf<String?>(null) }
    var eye by remember { mutableStateOf<ImageBitmap?>(null) }
    // Its replies, spoken on the TV: new clips since the page opened, in order
    val voice = remember { Omega7Voice(context) }
    val speech = remember { Channel<Long>(Channel.UNLIMITED) }
    val speak by rememberUpdatedState(voiceOn)
    var heardUpTo by remember { mutableStateOf<Long?>(null) }
    LaunchedEffect(client) {
        for (id in speech) {
            if (!speak) continue
            try {
                voice.play(client.speech(id))
            } catch (e: Omega7Exception) {
                AppLog.w("Omega7", "Couldn't fetch a reply: ${e.message}")
            }
        }
    }

    LaunchedEffect(client) {
        while (true) {
            try {
                val fresh = client.state()
                state = fresh
                problem = null
                // The first look only sets where to start, like the web remote: nothing old is replayed
                val newest = fresh.audioIds.maxOrNull()
                val heard = heardUpTo
                if (heard == null) {
                    heardUpTo = newest ?: 0L
                } else if (newest != null && newest > heard) {
                    fresh.audioIds.filter { it > heard }.sorted().forEach { speech.trySend(it) }
                    heardUpTo = newest
                }
                delay(STATE_POLL_MS)
            } catch (e: Omega7Exception) {
                problem = e.message
                if (e.loginRejected) {
                    onLoginRejected()
                    return@LaunchedEffect
                }
                delay(RETRY_MS)
            }
        }
    }
    LaunchedEffect(client) {
        while (true) {
            try {
                client.watchEye { eye = it }
            } catch (_: Omega7Exception) {
            }
            delay(RETRY_MS)
        }
    }

    fun act(label: String, action: suspend () -> Unit) {
        scope.launch {
            try {
                action()
                Toast.makeText(context, label, Toast.LENGTH_SHORT).show()
            } catch (e: Omega7Exception) {
                Toast.makeText(context, e.message, Toast.LENGTH_LONG).show()
            }
        }
    }

    Row(modifier = modifier, horizontalArrangement = Arrangement.spacedBy(20.dp)) {
        // The eye
        Column(
            modifier = Modifier.weight(0.9f).fillMaxHeight()
                .background(MaterialTheme.colorScheme.surfaceVariant).decoFrame().padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            PanelTitle("Ocular")
            Box(
                Modifier.weight(1f).aspectRatio(1f).drawBehind { drawEyeRing() }.padding(14.dp),
                contentAlignment = Alignment.Center,
            ) {
                val frame = eye
                if (frame != null) {
                    Image(frame, contentDescription = "Omega-7's eye", contentScale = ContentScale.Crop, modifier = Modifier.fillMaxSize().clip(CircleShape))
                } else {
                    MdiIcon("mdi:eye", size = 48.dp, color = Deco.Gold)
                }
            }
            Text((state?.name ?: "Omega-7").uppercase(), style = MaterialTheme.typography.headlineSmall.marquee(), color = Deco.GoldHi, modifier = Modifier.padding(top = 8.dp))
            Text(
                listOfNotNull(state?.mood?.takeIf { it.isNotEmpty() }, if (state?.silent == true) "SILENT" else null).joinToString(" · ").uppercase(),
                style = MaterialTheme.typography.labelSmall.copy(letterSpacing = 0.3.em),
                color = Deco.IvoryDim,
            )
            DecoOutlinedButton(onClick = { onVoiceChange(!voiceOn) }, modifier = Modifier.padding(top = 10.dp)) {
                MdiIcon(if (voiceOn) "mdi:volume-high" else "mdi:volume-off", size = 18.dp, color = androidx.tv.material3.LocalContentColor.current)
                Text(if (voiceOn) "Voice on TV" else "Voice off", modifier = Modifier.padding(start = 8.dp))
            }
        }
        // The vox log
        Column(
            modifier = Modifier.weight(1.2f).fillMaxHeight()
                .background(MaterialTheme.colorScheme.surfaceVariant).decoFrame().padding(16.dp),
        ) {
            PanelTitle("Vox log")
            val lines = state?.vox.orEmpty().takeLast(40)
            val list = rememberLazyListState()
            LaunchedEffect(lines.size) { if (lines.isNotEmpty()) list.scrollToItem(lines.lastIndex) }
            if (lines.isEmpty()) {
                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Text(problem ?: if (state == null) "Reaching Omega-7…" else "Nothing said yet", style = MaterialTheme.typography.bodySmall, color = Deco.IvoryDim, textAlign = TextAlign.Center)
                }
            } else {
                LazyColumn(state = list, verticalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxSize()) {
                    items(lines) { line ->
                        Column {
                            Text(
                                "${line.speaker.uppercase()}  ·  ${line.time}",
                                style = MaterialTheme.typography.labelSmall.copy(letterSpacing = 0.16.em),
                                color = if (line.speaker.startsWith("Omega", ignoreCase = true)) Deco.Gold else Deco.Sapphire,
                            )
                            Text(line.text, style = MaterialTheme.typography.bodySmall, color = Deco.Ivory)
                        }
                    }
                }
            }
        }
        // Vitals and controls
        Column(
            modifier = Modifier.weight(1f).fillMaxHeight()
                .background(MaterialTheme.colorScheme.surfaceVariant).decoFrame().padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            PanelTitle("Cogitator")
            val s = state
            if (s != null) {
                Vital("mdi:thermometer", "Core", s.temperature)
                Vital("mdi:chip", "CPU", s.cpu)
                Vital("mdi:memory", "Memory", s.ram)
                Vital("mdi:harddisk", "Storage", s.storage)
                Vital("mdi:power", "Power", s.power)
                Vital("mdi:robot", "Game", s.game)
            } else {
                Text(problem ?: "Reaching Omega-7…", style = MaterialTheme.typography.bodySmall, color = Deco.IvoryDim)
            }
            Spacer(Modifier.weight(1f))
            Box(Modifier.fillMaxWidth().padding(vertical = 4.dp)) { DecoDoubleRule() }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                DecoButton(onClick = { act("Omega-7 is listening") { client.wake() } }) {
                    MdiIcon("mdi:microphone", size = 18.dp, color = androidx.tv.material3.LocalContentColor.current)
                    Text("Wake", modifier = Modifier.padding(start = 6.dp))
                }
                var screensaverMenu by remember { mutableStateOf(false) }
                Box {
                    DecoOutlinedButton(onClick = { screensaverMenu = true }, enabled = s?.screensavers?.isNotEmpty() == true) { Text("Screensaver") }
                    if (screensaverMenu && s != null) {
                        ContextMenu(
                            title = "Screensaver",
                            actions = s.screensavers.map { name -> MenuAction(name) { act("Running $name") { client.screensaver(name) } } },
                            onDismiss = { screensaverMenu = false },
                        )
                    }
                }
            }
            CommandField { text -> act("Sent to Omega-7") { client.command(text) } }
            PresetCommands.forEach { (text, icon) ->
                DecoOutlinedButton(onClick = { act("Sent to Omega-7") { client.command(text) } }, modifier = Modifier.fillMaxWidth()) {
                    MdiIcon(icon, size = 18.dp, color = androidx.tv.material3.LocalContentColor.current)
                    Text(text, maxLines = 1, overflow = TextOverflow.Ellipsis, modifier = Modifier.padding(start = 8.dp))
                }
            }
        }
    }
}

@Composable
private fun Vital(icon: String, label: String, value: String) {
    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
        MdiIcon(icon, size = 18.dp, color = Deco.Gold)
        Text(label.uppercase(), style = MaterialTheme.typography.labelSmall.copy(letterSpacing = 0.16.em), color = Deco.IvoryDim, modifier = Modifier.weight(1f))
        Text(value.ifEmpty { "—" }, style = MaterialTheme.typography.labelLarge.figures(FontWeight.Normal), color = Deco.GoldHi, maxLines = 1)
    }
}

/** Type something for Omega-7 (the TV's keyboard comes up); OK on the keyboard sends it */
@Composable
private fun CommandField(onSend: (String) -> Unit) {
    var text by remember { mutableStateOf("") }
    val keyboard = LocalSoftwareKeyboardController.current
    TvTextField(
        value = text,
        onValueChange = { text = it },
        placeholder = "Say something to Omega-7…",
        keyboardType = KeyboardType.Text,
        imeAction = ImeAction.Send,
        onImeAction = {
            keyboard?.hide()
            if (text.isNotBlank()) onSend(text.trim())
            text = ""
        },
        modifier = Modifier.fillMaxWidth(),
    )
}

/** A gold ring with cog teeth around the eye */
private fun androidx.compose.ui.graphics.drawscope.DrawScope.drawEyeRing() {
    val c = Offset(size.width / 2, size.height / 2)
    val r = size.minDimension / 2
    drawCircle(Deco.Gold, r - 2.dp.toPx(), c, style = Stroke(2.dp.toPx()))
    drawCircle(Deco.Hair, r - 8.dp.toPx(), c, style = Stroke(1.dp.toPx()))
    val teeth = 24
    for (i in 0 until teeth) {
        val a = 2 * PI * i / teeth
        val d = Offset(cos(a).toFloat(), sin(a).toFloat())
        drawLine(Deco.Gold, c + d * (r - 2.dp.toPx()), c + d * (r + 4.dp.toPx()), 4.dp.toPx())
    }
}

/** Address and access code; Connect logs in and saves the session key and certificate */
@Composable
fun Omega7Dialog(initial: Omega7Server, onSave: (Omega7Server) -> Unit, onDismiss: () -> Unit) {
    // Where Omega-7 answered on this network when Marquee was set up; editable if it moves
    var url by remember { mutableStateOf(initial.url.ifEmpty { DEFAULT_OMEGA7_ADDRESS }) }
    var code by remember { mutableStateOf("") }
    var status by remember { mutableStateOf<String?>(null) }
    var connecting by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    val keyboard = LocalSoftwareKeyboardController.current
    val urlField = remember { FocusRequester() }
    val codeField = remember { FocusRequester() }
    val canConnect = normalizeOmega7Url(url) != null && code.isNotBlank()

    fun connect() {
        val baseUrl = normalizeOmega7Url(url) ?: return
        if (!canConnect || connecting) return
        keyboard?.hide()
        url = baseUrl
        status = "Connecting to $baseUrl…"
        connecting = true
        scope.launch {
            try {
                // The first connection is made here, by someone who knows this is their skull: its certificate is trusted from now on
                val client = Omega7Client(Omega7Server(baseUrl))
                val key = client.logIn(code)
                onSave(Omega7Server(baseUrl, key, client.seenCertPin))
                onDismiss()
            } catch (e: Omega7Exception) {
                status = e.message
            } finally {
                connecting = false
            }
        }
    }

    TopDialog(title = "Omega-7", onDismiss = onDismiss) {
        val fieldModifier = Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 4.dp)
        TvTextField(
            value = url,
            onValueChange = { url = it },
            placeholder = "Address, e.g. 192.168.0.40 or omega7 (uses port 8080)",
            keyboardType = KeyboardType.Uri,
            imeAction = ImeAction.Next,
            onImeAction = {
                keyboard?.hide()
                codeField.requestFocus()
            },
            modifier = fieldModifier.focusRequester(urlField),
        )
        TvTextField(
            value = code,
            onValueChange = { code = it },
            placeholder = "Access code shown on the eye",
            keyboardType = KeyboardType.Number,
            imeAction = ImeAction.Done,
            onImeAction = {
                keyboard?.hide()
                connect()
            },
            modifier = fieldModifier.focusRequester(codeField),
        )
        Row(
            modifier = Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 6.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            DecoButton(onClick = ::connect, enabled = canConnect) { Text("Connect") }
            if (initial.isSet) {
                DecoOutlinedButton(onClick = {
                    onSave(Omega7Server(initial.url))
                    onDismiss()
                }) { Text("Disconnect") }
            }
            Spacer(Modifier.weight(1f))
            DecoOutlinedButton(onClick = onDismiss) { Text("Close") }
        }
        Text(
            status ?: "Say \"Omega-7, show the web access code\": it shows a code on its eye for 10 minutes. The TV keeps the login after that.",
            style = MaterialTheme.typography.bodySmall,
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 8.dp),
        )
        LaunchedEffect(Unit) { codeField.requestFocus() }
    }
}
