package com.evofactory.homeboard

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.focusable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.em
import androidx.tv.material3.MaterialTheme
import androidx.tv.material3.Text
import kotlinx.coroutines.delay
import org.json.JSONArray
import org.json.JSONObject
import java.time.LocalDate
import java.time.OffsetDateTime
import java.time.ZoneId
import java.time.ZonedDateTime
import java.time.format.DateTimeFormatter
import java.time.format.DateTimeParseException
import java.util.Locale

/*
 * The Media page, like the dashboard's Media view: "Coming up" from the Sonarr and Radarr
 * calendars, and "Downloads" from SABnzbd, Sonarr and Jellyfin's sensors.
 */

val MediaCalendars = listOf("calendar.sonarr", "calendar.radarr")
private const val CALENDAR_DAYS = 14
private const val CALENDAR_REFRESH_MS = 15 * 60_000L

/** The sensors in the Downloads panel, in order, with the dashboard's names */
val DownloadSensors = listOf(
    Triple("sensor.sabnzbd_status", "SABnzbd", "mdi:download"),
    Triple("sensor.sabnzbd_speed", "Speed", "mdi:speedometer"),
    Triple("sensor.sabnzbd_queue_count", "In queue", "mdi:format-list-numbered"),
    Triple("sensor.sabnzbd_left_to_download", "Left", "mdi:progress-download"),
    Triple("sensor.sonarr_upcoming", "Upcoming episodes", "mdi:television-classic"),
    Triple("sensor.alexandria_jellyfin_active_clients", "Jellyfin viewers", "mdi:play-box"),
    Triple("sensor.sabnzbd_free_disk_space", "Array free", "mdi:harddisk"),
)

/** One calendar entry; [time] is null for all-day ones (Radarr's releases) */
class CalendarEvent(val calendar: String, val day: LocalDate, val time: ZonedDateTime?, val summary: String)

/** Events from now for [days] days, through Home Assistant's calendar.get_events (with return_response) */
suspend fun HaSession.calendarEvents(ids: List<String>, days: Int): List<CalendarEvent> {
    val result = command("call_service") {
        put("domain", "calendar")
        put("service", "get_events")
        put("target", JSONObject().put("entity_id", JSONArray(ids)))
        put("service_data", JSONObject().put("duration", JSONObject().put("days", days)))
        put("return_response", true)
    } as? JSONObject ?: return emptyList()
    val response = result.optJSONObject("response") ?: return emptyList()
    val zone = ZoneId.systemDefault()
    return ids.flatMap { id ->
        val events = response.optJSONObject(id)?.optJSONArray("events") ?: return@flatMap emptyList()
        (0 until events.length()).mapNotNull { events.optJSONObject(it) }.mapNotNull { event ->
            val start = event.optString("start")
            val summary = event.optString("summary").ifEmpty { return@mapNotNull null }
            if (start.length == 10) {
                runCatching { CalendarEvent(id, LocalDate.parse(start), null, summary) }.getOrNull()
            } else {
                try {
                    val time = OffsetDateTime.parse(start).atZoneSameInstant(zone)
                    CalendarEvent(id, time.toLocalDate(), time, summary)
                } catch (_: DateTimeParseException) {
                    null
                }
            }
        }
    }
        // Releases that began before today (all-day ones that run on) belong to days gone by
        .filter { !it.day.isBefore(LocalDate.now()) }
        .sortedWith(compareBy({ it.day }, { it.time?.toEpochSecond() ?: Long.MIN_VALUE }))
}

@Composable
fun MediaPage(connection: HaConnection?, modifier: Modifier = Modifier) {
    var events by remember { mutableStateOf<List<CalendarEvent>?>(null) }
    var problem by remember { mutableStateOf<String?>(null) }
    val session = connection?.session
    LaunchedEffect(session) {
        val live = session ?: return@LaunchedEffect
        while (true) {
            try {
                events = live.calendarEvents(MediaCalendars, CALENDAR_DAYS)
                problem = null
            } catch (e: HaException) {
                problem = e.message
            }
            delay(CALENDAR_REFRESH_MS)
        }
    }
    Row(modifier = modifier, horizontalArrangement = Arrangement.spacedBy(20.dp)) {
        Column(
            Modifier.weight(1.6f).fillMaxHeight().background(MaterialTheme.colorScheme.surfaceVariant).decoFrame().padding(16.dp),
        ) {
            PanelTitle("Coming up")
            val list = events
            when {
                connection == null -> Centered("Connect Home Assistant in Settings for the Sonarr and Radarr calendars")
                list == null -> Centered(problem ?: "Reading the calendars…")
                list.isEmpty() -> Centered("Nothing in the next two weeks")
                else -> ComingUp(list)
            }
        }
        Column(
            Modifier.weight(1f).fillMaxHeight().background(MaterialTheme.colorScheme.surfaceVariant).decoFrame().padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            PanelTitle("Downloads")
            if (connection == null) {
                Centered("Connect Home Assistant in Settings")
            } else {
                DownloadSensors.forEach { (id, name, icon) ->
                    val entity = connection.entities[id]
                    DownloadRow(entity?.icon?.takeIf { entity.attributes.has("icon") } ?: icon, name, entity?.reading ?: "—")
                }
            }
        }
    }
}

@Composable
private fun Centered(text: String) {
    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Text(text, style = MaterialTheme.typography.bodySmall, color = Deco.IvoryDim, textAlign = TextAlign.Center)
    }
}

/** Days as Poiret headings, their episodes and films under them; each line is selectable, so the remote can scroll */
@Composable
private fun ComingUp(events: List<CalendarEvent>) {
    val today = LocalDate.now()
    val dayFormat = DateTimeFormatter.ofPattern("EEEE · MMMM d", Locale.getDefault())
    val timeFormat = DateTimeFormatter.ofPattern("h:mm a", Locale.getDefault())
    val byDay = events.groupBy { it.day }
    LazyColumn(verticalArrangement = Arrangement.spacedBy(4.dp), modifier = Modifier.fillMaxSize()) {
        byDay.forEach { (day, dayEvents) ->
            item(key = "day-$day") {
                val label = when (day) {
                    today -> "Today"
                    today.plusDays(1) -> "Tomorrow"
                    else -> day.format(dayFormat)
                }
                Column(Modifier.padding(top = 8.dp)) {
                    Text(label.uppercase(), style = MaterialTheme.typography.titleMedium.marquee(), color = Deco.GoldHi)
                    Box(Modifier.padding(top = 2.dp).fillMaxWidth().height(1.dp).background(Deco.HairFaint))
                }
            }
            items(dayEvents, key = { "${it.calendar}-${it.day}-${it.summary}" }) { event ->
                var focused by remember { mutableStateOf(false) }
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                    modifier = Modifier
                        .fillMaxWidth()
                        .onFocusChanged { focused = it.isFocused }
                        .focusable()
                        .then(if (focused) Modifier.background(Deco.Gold.copy(alpha = 0.14f)).border(1.dp, Deco.GoldHi) else Modifier)
                        .padding(horizontal = 8.dp, vertical = 5.dp),
                ) {
                    MdiIcon(if (event.calendar.endsWith("radarr")) "mdi:movie-open" else "mdi:television-classic", size = 18.dp, color = Deco.Gold)
                    Text(
                        event.time?.format(timeFormat) ?: "All day",
                        style = MaterialTheme.typography.labelMedium.figures(FontWeight.Normal),
                        color = Deco.IvoryDim,
                        modifier = Modifier.width(72.dp),
                    )
                    Text(event.summary, style = MaterialTheme.typography.bodyMedium, color = Deco.Ivory, maxLines = 1, overflow = TextOverflow.Ellipsis)
                }
            }
        }
    }
}

/** Like the dashboard's deco_tile in a row: a diamond icon well, the name in capitals, the reading in Jost */
@Composable
private fun DownloadRow(icon: String, name: String, value: String) {
    Row(
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(14.dp),
        modifier = Modifier.fillMaxWidth().padding(vertical = 2.dp),
    ) {
        DiamondWell(icon)
        Text(name.uppercase(), style = MaterialTheme.typography.labelSmall.copy(letterSpacing = 0.14.em), color = Deco.IvoryDim, modifier = Modifier.weight(1f))
        Text(value, style = MaterialTheme.typography.titleMedium.figures(FontWeight.Normal), color = Deco.GoldHi, maxLines = 1)
    }
}

/** The dashboard's icon well: a square turned 45°, gold hairline, the icon upright inside */
@Composable
fun DiamondWell(icon: String, lit: Boolean = false, size: androidx.compose.ui.unit.Dp = 30.dp) {
    Box(contentAlignment = Alignment.Center, modifier = Modifier.size(size + 8.dp)) {
        Box(
            Modifier.size(size).rotate(45f)
                .background(if (lit) Deco.Gold.copy(alpha = 0.18f) else Deco.Ink.copy(alpha = 0.3f))
                .border(1.dp, if (lit) Deco.Gold else Deco.HairFaint),
        )
        MdiIcon(icon, size = size * 0.6f, color = if (lit) Deco.GoldHi else Deco.Gold)
    }
}
