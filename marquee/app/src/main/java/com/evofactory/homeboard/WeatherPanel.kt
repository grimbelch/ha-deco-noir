package com.evofactory.homeboard

import android.text.format.DateFormat
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.em
import androidx.compose.ui.unit.sp
import androidx.tv.material3.MaterialTheme
import androidx.tv.material3.Text
import java.time.LocalDate
import java.time.ZonedDateTime
import java.time.format.DateTimeFormatter
import java.time.temporal.ChronoUnit
import java.util.Locale
import kotlin.math.roundToInt

/** Followed even if not picked: the weather the Deco Noir dashboard's lobby shows */
const val DEFAULT_WEATHER_ENTITY = "weather.forecast_home"

private const val HOURS_SHOWN = 5
private const val DAYS_SHOWN = 5

/**
 * The weather panel: now (icon, temperature, condition, feels-like, high/low, humidity and wind),
 * the next hours and the next days, from Home Assistant's [weatherId].
 */
@Composable
fun WeatherPanel(connection: HaConnection?, weatherId: String, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .background(MaterialTheme.colorScheme.surfaceVariant)
            .decoFrame()
            .padding(horizontal = 18.dp, vertical = 14.dp),
    ) {
        PanelTitle("Weather")
        val entity = connection?.entities?.get(weatherId)
        when {
            connection == null -> PanelMessage("Connect Home Assistant in Settings for the weather")
            entity == null -> PanelMessage(
                when (connection.status) {
                    HaStatus.Connected -> "No $weatherId in Home Assistant. Pick a weather entity under Settings › Home Assistant › Choose sensors"
                    HaStatus.Offline -> "Home Assistant offline · retrying"
                    HaStatus.TokenRejected -> "Home Assistant rejected the login"
                    HaStatus.Connecting -> "Connecting to Home Assistant…"
                },
            )
            else -> WeatherContent(entity, connection.hourly[weatherId], connection.daily[weatherId])
        }
    }
}

/** A small "◆ TITLE ◆" in gold capitals at the top of a panel */
@Composable
fun PanelTitle(title: String) {
    Text(
        "◆  ${title.uppercase()}  ◆",
        style = MaterialTheme.typography.labelSmall.copy(letterSpacing = 0.3.em),
        color = Deco.Gold,
        modifier = Modifier.fillMaxWidth().padding(bottom = 6.dp),
        textAlign = TextAlign.Center,
    )
}

@Composable
private fun PanelMessage(text: String) {
    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Text(text, style = MaterialTheme.typography.bodySmall, color = Deco.IvoryDim, textAlign = TextAlign.Center)
    }
}

@Composable
private fun WeatherContent(entity: HaEntity, hourly: List<HaForecast>?, daily: List<HaForecast>?) {
    val context = LocalContext.current
    val condition = entity.state
    val attributes = entity.attributes
    val unit = attributes.optString("temperature_unit").ifEmpty { "°" }.let { if (it.startsWith("°")) "°" else it }
    fun deg(value: Double?) = value?.let { "${it.roundToInt()}$unit" } ?: "—"

    val today = daily?.firstOrNull { it.time?.toLocalDate() == LocalDate.now() } ?: daily?.firstOrNull()
    val feels = attributes.optDouble("apparent_temperature").takeUnless { it.isNaN() }
    val humidity = attributes.optDouble("humidity").takeUnless { it.isNaN() }
    val wind = attributes.optDouble("wind_speed").takeUnless { it.isNaN() }
    val windUnit = attributes.optString("wind_speed_unit")

    Column(Modifier.fillMaxSize(), verticalArrangement = Arrangement.SpaceBetween) {
        // Now: icon, temperature and condition, then the details across the panel
        Column {
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(14.dp)) {
                MdiIcon(weatherIcon(condition), size = 52.dp, color = Deco.GoldHi)
                Text(
                    deg(entity.temperature),
                    style = MaterialTheme.typography.displaySmall.figures(FontWeight.ExtraLight).copy(fontSize = 52.sp),
                    color = Deco.Ivory,
                )
                Text(
                    (weatherLabel(condition) ?: condition).uppercase(),
                    style = MaterialTheme.typography.labelMedium.copy(letterSpacing = 0.2.em),
                    color = Deco.GoldHi,
                    maxLines = 2,
                    modifier = Modifier.weight(1f),
                )
            }
            DetailLine(
                listOfNotNull(
                    today?.temperature?.let { "H ${deg(it)}" },
                    today?.lowTemperature?.let { "L ${deg(it)}" },
                    feels?.let { "Feels ${deg(it)}" },
                ),
            )
            DetailLine(
                listOfNotNull(
                    humidity?.let { "Humidity ${it.roundToInt()}%" },
                    wind?.let { "Wind ${it.roundToInt()} $windUnit".trim() },
                ),
            )
        }
        // Next hours
        val now = ZonedDateTime.now().truncatedTo(ChronoUnit.HOURS)
        val hours = hourly.orEmpty().filter { it.time?.isBefore(now) == false }.take(HOURS_SHOWN)
        if (hours.isNotEmpty()) {
            Rule()
            val hourFormat = DateTimeFormatter.ofPattern(if (DateFormat.is24HourFormat(context)) "HH:mm" else "h a", Locale.getDefault())
            ForecastRow(hours.map { hour ->
                Forecast(hour.time?.format(hourFormat).orEmpty().uppercase(), hour.condition, deg(hour.temperature))
            })
        }
        // Next days
        val days = daily.orEmpty().filter { it.time?.toLocalDate()?.isBefore(LocalDate.now()) == false }.take(DAYS_SHOWN)
        if (days.isNotEmpty()) {
            Rule()
            val dayFormat = DateTimeFormatter.ofPattern("EEE", Locale.getDefault())
            ForecastRow(days.mapIndexed { index, day ->
                val label = if (index == 0 && day.time?.toLocalDate() == LocalDate.now()) "TODAY" else day.time?.format(dayFormat).orEmpty().uppercase()
                Forecast(label, day.condition, deg(day.temperature), day.lowTemperature?.let(::deg))
            })
        }
    }
}

@Composable
private fun Rule() {
    Box(Modifier.fillMaxWidth().height(1.dp).background(Deco.HairFaint))
}

/** One column of a forecast row; [low] shows dimmed under [temperature] (days) */
private data class Forecast(val label: String, val condition: String?, val temperature: String, val low: String? = null)

@Composable
private fun DetailLine(parts: List<String>) {
    if (parts.isEmpty()) return
    Text(
        parts.joinToString("  ·  "),
        style = MaterialTheme.typography.labelMedium.figures(FontWeight.Normal),
        color = Deco.IvoryDim,
        maxLines = 1,
        overflow = TextOverflow.Ellipsis,
        modifier = Modifier.padding(top = 4.dp),
    )
}

/** Evenly spread columns: a label in gold capitals, the condition's icon, the temperature in Jost */
@Composable
private fun ForecastRow(items: List<Forecast>) {
    Row(Modifier.fillMaxWidth()) {
        items.forEach { item ->
            Column(Modifier.weight(1f), horizontalAlignment = Alignment.CenterHorizontally) {
                Text(item.label, style = MaterialTheme.typography.labelSmall.copy(letterSpacing = 0.04.em), color = Deco.Gold, maxLines = 1)
                MdiIcon(weatherIcon(item.condition), size = 22.dp, color = Deco.GoldHi, modifier = Modifier.padding(vertical = 3.dp))
                Text(item.temperature, style = MaterialTheme.typography.labelLarge.figures(FontWeight.Normal), color = Deco.Ivory, maxLines = 1)
                item.low?.let {
                    Text(it, style = MaterialTheme.typography.labelMedium.figures(FontWeight.Normal), color = Deco.IvoryFaint, maxLines = 1)
                }
            }
        }
    }
}
