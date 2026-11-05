package com.evofactory.homeboard

import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.text.format.DateFormat
import android.widget.Toast
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.key
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.produceState
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clipToBounds
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusProperties
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.RectangleShape
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.em
import androidx.compose.ui.unit.sp
import androidx.tv.material3.Border
import androidx.tv.material3.ClickableSurfaceDefaults
import androidx.tv.material3.Glow
import androidx.tv.material3.MaterialTheme
import androidx.tv.material3.Surface
import androidx.tv.material3.Text
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import java.util.Calendar
import java.util.Date
import java.util.Locale
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.roundToInt
import kotlin.math.sin

/*
 * Marquee's Home tab, laid out like the Deco Noir "Home" dashboard view: a lobby header (clock,
 * date, greeting, weather and status chips), a row of scenes under a ◆ SCENES ◆ marquee heading,
 * and, on the right, Jellyfin's "Now Showing" marquee, with the main camera under it if there is one.
 */

const val JELLYFIN_PACKAGE = "org.jellyfin.androidtv"

/**
 * The Home tab. [camera] draws the main camera into the modifier it's given; null without one.
 * [scenesFocus] selects the first scene, [jellyfinFocus] the Jellyfin marquee. Up from the
 * marquee goes to [upFocus] (the top bar's right end), down from the scenes, marquee and camera to
 * [downFocus] (the app row). [onSetUpHa] opens the Home Assistant login.
 */
@Composable
fun LobbyHome(
    haConnection: HaConnection?,
    entityIds: List<String>,
    actionIds: List<String>,
    camera: (@Composable (Modifier) -> Unit)?,
    cameraFocus: FocusRequester,
    scenesFocus: FocusRequester,
    jellyfinFocus: FocusRequester,
    upFocus: FocusRequester,
    downFocus: FocusRequester,
    onSetUpHa: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val scenes = if (haConnection != null) actionIds else emptyList()
    Row(modifier = modifier, horizontalArrangement = Arrangement.spacedBy(EdgePadding)) {
        Column(
            modifier = Modifier.weight(LOBBY_WEIGHT).fillMaxHeight(),
            verticalArrangement = Arrangement.spacedBy(PanelItemSpacing),
        ) {
            LobbyCard(
                haConnection = haConnection,
                entityIds = entityIds,
                onSetUpHa = onSetUpHa,
                setUpModifier = Modifier.focusProperties { down = downFocus },
                modifier = Modifier.weight(1f).fillMaxWidth(),
            )
            if (scenes.isNotEmpty() && haConnection != null) {
                MarqueeHeading("Scenes")
                Row(horizontalArrangement = Arrangement.spacedBy(PanelItemSpacing)) {
                    scenes.forEachIndexed { index, id ->
                        key(id) {
                            SceneTile(
                                connection = haConnection,
                                id = id,
                                modifier = Modifier
                                    .weight(1f)
                                    .then(if (index == 0) Modifier.focusRequester(scenesFocus) else Modifier)
                                    .focusProperties {
                                        down = downFocus
                                        if (index == scenes.lastIndex) right = jellyfinFocus
                                    },
                            )
                        }
                    }
                }
            }
        }
        BoxWithConstraints(modifier = Modifier.weight(1f).fillMaxHeight()) {
            // With a camera, the marquee keeps a strip at the top and the camera takes the rest at 16:9
            val cameraHeight = if (camera != null) {
                minOf(maxWidth * 9f / 16f, maxHeight - JellyfinStripHeight - PanelItemSpacing)
            } else {
                0.dp
            }
            Column(verticalArrangement = Arrangement.spacedBy(PanelItemSpacing)) {
                JellyfinMarquee(
                    compact = camera != null,
                    modifier = Modifier
                        .fillMaxWidth()
                        .weight(1f)
                        .focusRequester(jellyfinFocus)
                        .focusProperties {
                            up = upFocus
                            down = if (camera != null) cameraFocus else downFocus
                        },
                )
                camera?.invoke(
                    Modifier
                        .width(cameraHeight * 16f / 9f)
                        .height(cameraHeight)
                        .align(Alignment.End)
                        .focusRequester(cameraFocus)
                        .focusProperties {
                            up = jellyfinFocus
                            down = downFocus
                        },
                )
            }
        }
    }
}

/** Share of the width the lobby takes, against 1 for the Jellyfin column; see FIRST_SLOT_UNDER_PANEL */
const val LOBBY_WEIGHT = 1.35f

private val JellyfinStripHeight = 72.dp

/** "◆ TITLE ◆" between two gold hairlines, like the dashboard's deco_marquee headings */
@Composable
fun MarqueeHeading(title: String, modifier: Modifier = Modifier) {
    Row(modifier = modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
        Box(Modifier.weight(1f).height(1.dp).background(Brush.horizontalGradient(listOf(Color.Transparent, Deco.Hair))))
        Text(
            "◆   ${title.uppercase()}   ◆",
            style = MaterialTheme.typography.titleMedium.marquee(),
            color = Deco.GoldHi,
            modifier = Modifier.padding(horizontal = 14.dp),
        )
        Box(Modifier.weight(1f).height(1.dp).background(Brush.horizontalGradient(listOf(Deco.Hair, Color.Transparent))))
    }
}

/** The lobby header: the time large in Jost, the date in gold capitals, a Poiret greeting; weather on the right, chips below */
@Composable
private fun LobbyCard(
    haConnection: HaConnection?,
    entityIds: List<String>,
    onSetUpHa: () -> Unit,
    setUpModifier: Modifier,
    modifier: Modifier = Modifier,
) {
    val context = LocalContext.current
    val now by produceState(Date()) {
        while (true) {
            value = Date()
            delay(60_000 - System.currentTimeMillis() % 60_000 + 50)
        }
    }
    val is24h = DateFormat.is24HourFormat(context)
    val calendar = Calendar.getInstance().apply { time = now }
    val hour = calendar.get(Calendar.HOUR_OF_DAY)
    val minute = "%02d".format(calendar.get(Calendar.MINUTE))
    val time = if (is24h) "$hour:$minute" else "${(hour % 12).let { if (it == 0) 12 else it }}:$minute"
    val date = DateFormat.format("EEEE · MMMM d", now).toString().uppercase(Locale.getDefault())
    val greeting = when {
        hour < 5 -> "Good night"
        hour < 12 -> "Good morning"
        hour < 17 -> "Good afternoon"
        else -> "Good evening"
    }
    val entities = haConnection?.entities
    val weatherId = entityIds.firstOrNull(::isHaWeather)
    val chipIds = entityIds.filterNot { isHaAction(it) || isHaWeather(it) }

    Column(
        modifier = modifier
            .background(MaterialTheme.colorScheme.surfaceVariant)
            .drawBehind { drawLobbyFan() }
            .decoFrame()
            .padding(horizontal = 22.dp, vertical = 18.dp),
    ) {
        Row(modifier = Modifier.fillMaxWidth(), verticalAlignment = Alignment.Bottom) {
            Column(modifier = Modifier.weight(1f)) {
                Row(verticalAlignment = Alignment.Bottom) {
                    Text(
                        time,
                        style = MaterialTheme.typography.displayMedium.figures(FontWeight.ExtraLight).copy(fontSize = 64.sp, lineHeight = 60.sp),
                        color = Deco.Ivory,
                    )
                    if (!is24h) {
                        Text(
                            if (hour < 12) "AM" else "PM",
                            style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Light, letterSpacing = 0.3.em),
                            color = Deco.GoldHi,
                            modifier = Modifier.padding(start = 8.dp, bottom = 10.dp),
                        )
                    }
                }
                Text(
                    date,
                    style = MaterialTheme.typography.labelMedium.copy(letterSpacing = 0.38.em, fontWeight = FontWeight.Normal),
                    color = Deco.GoldHi,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                    modifier = Modifier.padding(top = 10.dp),
                )
                Text(
                    greeting,
                    style = MaterialTheme.typography.headlineSmall.copy(fontSize = 26.sp),
                    color = Deco.Ivory,
                    modifier = Modifier.padding(top = 6.dp),
                )
            }
            if (weatherId != null && entities != null) LobbyWeather(entities[weatherId], haConnection?.daily?.get(weatherId))
        }
        Spacer(Modifier.weight(1f))
        Box(Modifier.padding(top = 12.dp).fillMaxWidth().height(1.dp).background(Deco.HairFaint))
        Box(Modifier.padding(top = 12.dp).fillMaxWidth().clipToBounds()) {
            when {
                haConnection == null -> DecoOutlinedButton(onClick = onSetUpHa, modifier = setUpModifier) {
                    Text("Connect Home Assistant")
                }
                haConnection.status == HaStatus.TokenRejected -> DecoOutlinedButton(onClick = onSetUpHa, modifier = setUpModifier) {
                    Text("Home Assistant rejected the login · Log in again")
                }
                // Nothing picked means nothing to connect for, so no status either
                chipIds.isEmpty() -> Text(
                    (if (entityIds.isEmpty()) null else statusLine(haConnection))
                        ?: "Choose sensors and scenes in Settings › Home Assistant to show them here",
                    style = MaterialTheme.typography.labelSmall,
                    color = FaintText,
                )
                else -> LobbyChips(chipIds, haConnection)
            }
        }
    }
}

private fun statusLine(connection: HaConnection): String? = when (connection.status) {
    HaStatus.Connecting -> "Connecting to Home Assistant…"
    HaStatus.Offline -> "Home Assistant offline · retrying"
    else -> null
}

/** Weather like the lobby's: a gold icon, the temperature large in Jost, then condition · high / low in capitals */
@Composable
private fun LobbyWeather(entity: HaEntity?, daily: List<HaForecast>?) {
    entity ?: return
    val condition = entity.state
    val today = daily?.firstOrNull()
    val range = listOfNotNull(
        today?.temperature?.let { "H ${it.roundToInt()}°" },
        today?.lowTemperature?.let { "L ${it.roundToInt()}°" },
    ).joinToString(" · ")
    Column(horizontalAlignment = Alignment.End) {
        MdiIcon(weatherIcon(condition), size = 44.dp, color = Deco.GoldHi)
        Text(
            entity.temperature?.let { "${it.roundToInt()}°" } ?: "—",
            style = MaterialTheme.typography.displaySmall.figures(FontWeight.ExtraLight),
            color = Deco.Ivory,
        )
        Text(
            listOfNotNull(weatherLabel(condition), range.ifEmpty { null }).joinToString(" · ").uppercase(),
            style = MaterialTheme.typography.labelSmall.copy(letterSpacing = 0.26.em),
            color = Deco.IvoryDim,
            textAlign = TextAlign.End,
        )
    }
}

/** The picked sensors as chips: gold icon, NAME, reading in gold-hi Jost */
@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun LobbyChips(ids: List<String>, connection: HaConnection) {
    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        ids.forEach { id ->
            val entity = connection.entities[id]
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(7.dp),
                modifier = Modifier
                    .background(Deco.Ink.copy(alpha = 0.55f))
                    .border(1.dp, Deco.HairFaint)
                    .padding(horizontal = 10.dp, vertical = 5.dp),
            ) {
                MdiIcon(entity?.icon ?: "", size = 16.dp, color = Deco.Gold)
                Text(
                    (entity?.name ?: id).uppercase(),
                    style = MaterialTheme.typography.labelSmall,
                    color = Deco.IvoryDim,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                    modifier = Modifier.padding(top = 1.dp),
                )
                Text(
                    entity?.reading ?: "—",
                    style = MaterialTheme.typography.labelLarge.figures(FontWeight.Normal),
                    color = Deco.GoldHi,
                    maxLines = 1,
                )
            }
        }
    }
}

/** A faint gold fan rising from the lobby's bottom-right corner */
private fun androidx.compose.ui.graphics.drawscope.DrawScope.drawLobbyFan() {
    val origin = Offset(size.width, size.height)
    val reach = size.height * 1.1f
    val line = Deco.Gold.copy(alpha = 0.07f)
    for (k in 0..9) {
        val a = PI + PI / 2 * k / 9
        drawLine(line, origin, origin + Offset(cos(a).toFloat(), sin(a).toFloat()) * reach, 1f)
    }
    for (r in listOf(0.35f, 0.6f, 0.85f)) {
        drawCircle(line, reach * r, origin, style = androidx.compose.ui.graphics.drawscope.Stroke(1f))
    }
}

/** A scene or script, like the dashboard's deco_scene: a gold icon over its name in spaced capitals; OK runs it */
@Composable
private fun SceneTile(connection: HaConnection, id: String, modifier: Modifier = Modifier) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var running by remember { mutableStateOf(false) }
    val entity = connection.entities[id]
    val session = connection.session
    val domainIcon = defaultHaIcon(id.substringBefore('.'), null, "")
    val colors = MaterialTheme.colorScheme
    Surface(
        onClick = {
            if (session == null || running) return@Surface
            running = true
            scope.launch {
                try {
                    session.run(id)
                } catch (e: HaException) {
                    Toast.makeText(context, e.message, Toast.LENGTH_LONG).show()
                } finally {
                    running = false
                }
            }
        },
        modifier = modifier.height(SceneTileHeight),
        shape = ClickableSurfaceDefaults.shape(RectangleShape),
        colors = ClickableSurfaceDefaults.colors(
            containerColor = colors.surfaceVariant,
            contentColor = if (session != null && !running) Deco.GoldHi else Deco.GoldHi.copy(alpha = 0.45f),
            focusedContainerColor = colors.inverseSurface,
            focusedContentColor = colors.inverseOnSurface,
        ),
        border = ClickableSurfaceDefaults.border(
            border = Border(BorderStroke(1.dp, Deco.Hair), shape = RectangleShape),
            focusedBorder = Border(BorderStroke(1.dp, Deco.GoldHi), shape = RectangleShape),
        ),
        glow = ClickableSurfaceDefaults.glow(focusedGlow = Glow(Deco.Gold.copy(alpha = 0.45f), 10.dp)),
    ) {
        Column(
            modifier = Modifier.fillMaxSize().padding(horizontal = 6.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center,
        ) {
            MdiIcon(entity?.icon ?: domainIcon, fallback = domainIcon, size = 26.dp, color = androidx.tv.material3.LocalContentColor.current)
            Text(
                (entity?.name ?: id).uppercase(),
                style = MaterialTheme.typography.labelSmall.copy(letterSpacing = 0.2.em),
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
                modifier = Modifier.padding(top = 6.dp),
            )
        }
    }
}

private val SceneTileHeight = 64.dp

/**
 * Jellyfin as a cinema marquee: a sunburst crown, "◆ NOW SHOWING ◆", JELLYFIN in Poiret One and a
 * border of marquee bulbs that chase while the remote is on it. OK opens Jellyfin, or its store
 * page if it isn't installed. [compact] is the one-line strip shown above a camera.
 */
@Composable
private fun JellyfinMarquee(compact: Boolean, modifier: Modifier = Modifier) {
    val context = LocalContext.current
    var focused by remember { mutableStateOf(false) }
    val chase by rememberInfiniteTransition(label = "bulbs").animateFloat(
        initialValue = 0f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(tween(BULB_CHASE_MS, easing = LinearEasing), RepeatMode.Restart),
        label = "chase",
    )
    val installed = remember { context.packageManager.jellyfinLaunchIntent() != null }
    Surface(
        onClick = { context.openJellyfin() },
        modifier = modifier.onFocusChanged { focused = it.isFocused },
        shape = ClickableSurfaceDefaults.shape(RectangleShape),
        scale = ClickableSurfaceDefaults.scale(focusedScale = 1.02f),
        colors = ClickableSurfaceDefaults.colors(
            containerColor = Deco.Raised,
            contentColor = Deco.GoldHi,
            focusedContainerColor = Color(0xFF1F1A10),
            focusedContentColor = Deco.GoldHi,
        ),
        border = ClickableSurfaceDefaults.border(
            border = Border(BorderStroke(1.dp, Deco.Hair), shape = RectangleShape),
            focusedBorder = Border(BorderStroke(2.dp, Deco.GoldHi), shape = RectangleShape),
        ),
        glow = ClickableSurfaceDefaults.glow(focusedGlow = Glow(Deco.Gold.copy(alpha = 0.5f), 16.dp)),
    ) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .drawBehind {
                    drawMarqueeCrown(compact)
                    drawBulbs(if (focused) chase else -1f, if (compact) 9.dp else 12.dp)
                },
            contentAlignment = Alignment.Center,
        ) {
            if (compact) {
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                    Text("◆ NOW SHOWING ◆", style = MaterialTheme.typography.labelSmall.copy(letterSpacing = 0.3.em), color = Deco.Gold)
                    Text("JELLYFIN", style = MaterialTheme.typography.headlineSmall.marquee(), color = Deco.GoldHi)
                }
            } else {
                Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.padding(horizontal = 28.dp)) {
                    Text("◆   NOW SHOWING   ◆", style = MaterialTheme.typography.labelMedium.copy(letterSpacing = 0.34.em), color = Deco.Gold)
                    Box(Modifier.padding(vertical = 10.dp).width(180.dp)) { DecoDoubleRule(color = Deco.Hair) }
                    Text(
                        "JELLYFIN",
                        style = MaterialTheme.typography.displaySmall.marquee().copy(fontSize = 52.sp, letterSpacing = 0.16.em),
                        color = Deco.GoldHi,
                        maxLines = 1,
                    )
                    Box(Modifier.padding(vertical = 10.dp).width(180.dp)) { DecoDoubleRule(color = Deco.Hair) }
                    Text(
                        if (installed) "MOVIES · SHOWS · MUSIC" else "INSTALL JELLYFIN",
                        style = MaterialTheme.typography.labelSmall.copy(letterSpacing = 0.3.em),
                        color = Deco.IvoryDim,
                    )
                }
            }
        }
    }
}

private const val BULB_CHASE_MS = 2_400

/** Sunburst rays fanning down from the top centre, behind the title */
private fun androidx.compose.ui.graphics.drawscope.DrawScope.drawMarqueeCrown(compact: Boolean) {
    val center = Offset(size.width / 2, if (compact) size.height * 1.4f else -size.height * 0.08f)
    val reach = size.width.coerceAtLeast(size.height) * 1.2f
    val rays = Brush.radialGradient(
        listOf(Deco.Gold.copy(alpha = 0.22f), Deco.Gold.copy(alpha = 0f)),
        center = center,
        radius = reach * 0.85f,
    )
    val count = 26
    for (i in 0..count) {
        val a = if (compact) PI + PI * i / count else PI * i / count
        drawLine(rays, center, center + Offset(cos(a).toFloat(), sin(a).toFloat()) * reach, 1.2f)
    }
    drawCircle(Deco.Gold.copy(alpha = 0.12f), size.height * 0.18f, center, style = androidx.compose.ui.graphics.drawscope.Stroke(1f))
}

/**
 * Marquee bulbs around the inside of the border, every [spacing]. Lit softly at rest; when
 * [chase] is 0..1, a bright wave runs around them.
 */
private fun androidx.compose.ui.graphics.drawscope.DrawScope.drawBulbs(chase: Float, spacing: Dp) {
    val step = spacing.toPx()
    val inset = 8.dp.toPx()
    val radius = 2.dp.toPx()
    val w = size.width - 2 * inset
    val h = size.height - 2 * inset
    val perimeter = 2 * (w + h)
    val n = (perimeter / step).toInt().coerceAtLeast(4)
    for (i in 0 until n) {
        var d = perimeter * i / n
        val p = when {
            d < w -> Offset(inset + d, inset)
            d < w + h -> { d -= w; Offset(inset + w, inset + d) }
            d < 2 * w + h -> { d -= w + h; Offset(inset + w - d, inset + h) }
            else -> { d -= 2 * w + h; Offset(inset, inset + h - d) }
        }
        val lit = if (chase < 0f) {
            0.35f
        } else {
            // Every third bulb leads, like a theatre chaser
            val phase = ((i.toFloat() / 3f) - chase * 3f).mod(1f)
            0.35f + 0.65f * (1f - phase).let { it * it }
        }
        drawCircle(Deco.GoldHi.copy(alpha = lit * 0.5f), radius * 2.2f, p)
        drawCircle(Deco.GoldHi.copy(alpha = lit), radius, p)
    }
}

private fun android.content.pm.PackageManager.jellyfinLaunchIntent(): Intent? =
    getLeanbackLaunchIntentForPackage(JELLYFIN_PACKAGE) ?: getLaunchIntentForPackage(JELLYFIN_PACKAGE)

/** Opens Jellyfin; if it isn't installed, its page in the Amazon Appstore or Google Play */
private fun Context.openJellyfin() {
    packageManager.jellyfinLaunchIntent()?.let {
        startActivity(it.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
        return
    }
    val stores = listOf("amzn://apps/android?p=$JELLYFIN_PACKAGE", "market://details?id=$JELLYFIN_PACKAGE")
    for (store in stores) {
        try {
            startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(store)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
            return
        } catch (e: ActivityNotFoundException) {
            AppLog.i("Lobby", "No store for $store")
        }
    }
    Toast.makeText(this, "Install Jellyfin from your TV's app store", Toast.LENGTH_LONG).show()
}
