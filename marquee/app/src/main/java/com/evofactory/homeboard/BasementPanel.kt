package com.evofactory.homeboard

import android.widget.Toast
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.background
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.RectangleShape
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.em
import androidx.tv.material3.Border
import androidx.tv.material3.ClickableSurfaceDefaults
import androidx.tv.material3.Glow
import androidx.tv.material3.LocalContentColor
import androidx.tv.material3.MaterialTheme
import androidx.tv.material3.Surface
import androidx.tv.material3.Text
import kotlinx.coroutines.launch

/** The lower floor's lights, as on the dashboard's floor plan: entity, name, icon */
val BasementLights = listOf(
    Triple("switch.torch_light_front", "Torch front", "mdi:torch"),
    Triple("switch.torch_light_back", "Torch back", "mdi:torch"),
    Triple("switch.basement_fireplace_lights", "Fireplace", "mdi:fireplace"),
    Triple("switch.painting_desk", "Painting desk", "mdi:desk-lamp"),
)

/**
 * The basement's lights as Deco tiles, two by two: OK toggles one; a lit one glows like a sconce.
 * All on / All off below.
 */
@Composable
fun BasementPanel(connection: HaConnection?, modifier: Modifier = Modifier) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    fun call(service: String, ids: List<String>) {
        val session = connection?.session ?: return
        scope.launch {
            try {
                ids.forEach { session.callService(it.substringBefore('.'), service, it) }
            } catch (e: HaException) {
                Toast.makeText(context, e.message, Toast.LENGTH_LONG).show()
            }
        }
    }
    Column(
        modifier = modifier
            .background(MaterialTheme.colorScheme.surfaceVariant)
            .decoFrame()
            .padding(horizontal = 16.dp, vertical = 14.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        PanelTitle("Basement")
        if (connection == null) {
            Text("Connect Home Assistant in Settings for the lights", style = MaterialTheme.typography.bodySmall, color = Deco.IvoryDim)
            return@Column
        }
        BasementLights.chunked(2).forEach { pair ->
            Row(Modifier.weight(1f).fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                pair.forEach { (id, name, icon) ->
                    LightTile(connection.entities[id], name, icon, Modifier.weight(1f).fillMaxHeight()) { call("toggle", listOf(id)) }
                }
            }
        }
        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            val ids = BasementLights.map { it.first }
            DecoOutlinedButton(onClick = { call("turn_on", ids) }, modifier = Modifier.weight(1f)) {
                MdiIcon("mdi:lightbulb-group", size = 18.dp, color = LocalContentColor.current)
                Text("All on", modifier = Modifier.padding(start = 8.dp))
            }
            DecoOutlinedButton(onClick = { call("turn_off", ids) }, modifier = Modifier.weight(1f)) {
                MdiIcon("mdi:lightbulb-group-off", size = 18.dp, color = LocalContentColor.current)
                Text("All off", modifier = Modifier.padding(start = 8.dp))
            }
        }
    }
}

/** The dashboard's deco_tile: diamond well, name in capitals, ON / OFF; lit, it glows gold */
@Composable
private fun LightTile(entity: HaEntity?, name: String, icon: String, modifier: Modifier, onToggle: () -> Unit) {
    val on = entity?.state == "on"
    val unavailable = entity == null || entity.state == "unavailable"
    var focused by remember { mutableStateOf(false) }
    // Set here rather than through the Surface's content colors, which didn't reach the text when selected
    val text = if (focused) Deco.GoldHi else Deco.Ivory
    Surface(
        onClick = onToggle,
        modifier = modifier.onFocusChanged { focused = it.isFocused },
        shape = ClickableSurfaceDefaults.shape(RectangleShape),
        colors = ClickableSurfaceDefaults.colors(
            containerColor = if (on) Deco.Gold.copy(alpha = 0.10f) else Deco.Ink.copy(alpha = 0.35f),
            contentColor = Deco.Ivory,
            // Dark under the remote, so the gold well still reads; the border and halo say it's selected
            focusedContainerColor = Deco.Raised,
            focusedContentColor = Deco.Ivory,
        ),
        border = ClickableSurfaceDefaults.border(
            border = Border(BorderStroke(1.dp, if (on) Deco.Gold.copy(alpha = 0.55f) else Deco.HairFaint), shape = RectangleShape),
            focusedBorder = Border(BorderStroke(2.dp, Deco.GoldHi), shape = RectangleShape),
        ),
        glow = ClickableSurfaceDefaults.glow(
            glow = if (on) Glow(Deco.Gold.copy(alpha = 0.25f), 8.dp) else Glow.None,
            focusedGlow = Glow(Deco.Gold.copy(alpha = 0.45f), 10.dp),
        ),
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .then(if (on) Modifier.background(Brush.radialGradient(listOf(Deco.Gold.copy(alpha = 0.20f), Deco.Gold.copy(alpha = 0f)))) else Modifier)
                .padding(10.dp),
            verticalArrangement = Arrangement.Center,
        ) {
            DiamondWell(entity?.icon?.takeIf { entity.attributes.has("icon") } ?: icon, lit = on, size = 26.dp)
            Text(
                name.uppercase(),
                style = MaterialTheme.typography.labelSmall.copy(letterSpacing = 0.12.em),
                color = text.copy(alpha = if (on || focused) 1f else 0.7f),
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
                modifier = Modifier.padding(top = 6.dp),
            )
            Text(
                when {
                    unavailable -> "Unavailable"
                    on -> "On"
                    else -> "Off"
                }.uppercase(),
                style = MaterialTheme.typography.labelSmall.copy(letterSpacing = 0.2.em),
                color = if (on) Deco.GoldHi else text.copy(alpha = 0.55f),
            )
        }
    }
}
