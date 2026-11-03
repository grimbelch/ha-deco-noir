package com.evofactory.homeboard

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.draw.drawWithContent
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.RectangleShape
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontVariation
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.em
import androidx.tv.material3.Border
import androidx.tv.material3.Button
import androidx.tv.material3.ButtonDefaults
import androidx.tv.material3.CardBorder
import androidx.tv.material3.CardDefaults
import androidx.tv.material3.CardGlow
import androidx.tv.material3.CardShape
import androidx.tv.material3.Glow
import androidx.tv.material3.MaterialTheme
import androidx.tv.material3.OutlinedButton
import androidx.tv.material3.OutlinedButtonDefaults
import androidx.tv.material3.Shapes
import androidx.tv.material3.Typography
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.sin

/*
 * Marquee's Art Deco kit: the Deco Noir Home Assistant theme (themes/deco_noir.yaml at the repo
 * root) translated to Compose for TV. Same tokens, same ornaments: smoked glass over a gold
 * sunburst, hairline frames with stepped corner brackets, Poiret One marquee titles, Josefin Sans
 * labels and Jost figures.
 */

/** The Deco Noir tokens, named as in deco_noir.yaml (deco-ink → Deco.Ink, …) */
object Deco {
    val Ink = Color(0xFF0B0B0E)
    val Midnight = Color(0xFF11131C)
    val Ivory = Color(0xFFEDE6D6)
    val Gold = Color(0xFFC9A44C)
    val GoldHi = Color(0xFFE6CF9A)
    val Emerald = Color(0xFF3E9C82)
    val Sapphire = Color(0xFF5A79C8)
    val Garnet = Color(0xFFCF5B6B)
    val Warning = Color(0xFFD9A441)

    /** Gold dimmed for fills that must read on both the dark dialog and a gold-hi selected row (switch tracks, ticked boxes) */
    val GoldDeep = Color(0xFF8A6D2C)

    /** deco-hair / deco-hair-faint: the gold hairlines */
    val Hair = Gold.copy(alpha = 0.38f)
    val HairFaint = Gold.copy(alpha = 0.16f)

    /** deco_noir_lite's card surface: a TV has no backdrop blur, so the glass is the opaque-ish Lite one */
    val Glass = Color(0xDB101016)

    /** mdc-theme-surface: menus and dialogs */
    val Raised = Color(0xFF1C1A17)

    /** A step above Raised: buttons and panels inside a dialog */
    val RaisedHi = Color(0xFF29251E)

    /** secondary-text-color (ivory at 62%) and ivory at 45%, flattened onto ink */
    val IvoryDim = Color(0xFF97938A)
    val IvoryFaint = Color(0xFF716E68)

    /** mdc-dialog-scrim-color */
    val Scrim = Color(0xB8050508)

    val Poiret = FontFamily(Font(R.font.deco_poiret))
    val Josefin = FontFamily(
        josefin(FontWeight.Light),
        josefin(FontWeight.Normal),
        josefin(FontWeight.SemiBold),
    )
    val Jost = FontFamily(
        jost(FontWeight.ExtraLight),
        jost(FontWeight.Light),
        jost(FontWeight.Normal),
    )

    private fun josefin(weight: FontWeight) =
        Font(R.font.deco_josefin, weight, variationSettings = FontVariation.Settings(FontVariation.weight(weight.weight)))

    private fun jost(weight: FontWeight) =
        Font(R.font.deco_jost, weight, variationSettings = FontVariation.Settings(FontVariation.weight(weight.weight)))

    /** Section titles and tabs: Poiret One in spaced capitals, like the dashboard's marquee headings */
    val MarqueeLetterSpacing = 0.14.em

    /** Corner brackets: 16px arms, 2px thick (card-mod-card ::after) */
    val BracketArm = 16.dp
    val BracketWidth = 2.dp
}

/** Square corners everywhere, like ha-card-border-radius: 0 */
private val Square = RoundedCornerShape(0.dp)
val DecoShapes = Shapes(extraSmall = Square, small = Square, medium = Square, large = Square, extraLarge = Square)

/** Round buttons become cut-corner "octagon" wells: the Deco answer to a circle that still holds an icon */
val DecoWellShape = CutCornerShape(28)

/** Text buttons: square-shouldered with clipped corners, like a theatre ticket */
val DecoButtonShape = CutCornerShape(6.dp)

/** Tiles and cards: square, a faint hairline at rest, gold-hi with a gold halo when the remote is on them */
val DecoCardShape: CardShape
    @Composable get() = CardDefaults.shape(RectangleShape)

val DecoCardGlow: CardGlow
    @Composable get() = CardDefaults.glow(focusedGlow = Glow(Deco.Gold.copy(alpha = 0.45f), 12.dp))

val DecoCardBorder: CardBorder
    @Composable get() = CardDefaults.border(
        border = Border(BorderStroke(1.dp, Deco.HairFaint), shape = RectangleShape),
        focusedBorder = Border(BorderStroke(3.dp, Deco.GoldHi), shape = RectangleShape),
        pressedBorder = Border(BorderStroke(3.dp, Deco.Gold), shape = RectangleShape),
    )

/** Josefin Sans for reading, Poiret One for display sizes, labels spaced like small caps */
val DecoTypography: Typography = Typography().run {
    fun TextStyle.poiret() = copy(fontFamily = Deco.Poiret, fontWeight = FontWeight.Normal, letterSpacing = 0.06.em)
    fun TextStyle.josefin(weight: FontWeight = FontWeight.Normal, spacing: Double = 0.02) =
        copy(fontFamily = Deco.Josefin, fontWeight = weight, letterSpacing = spacing.em)
    copy(
        displayLarge = displayLarge.poiret(),
        displayMedium = displayMedium.poiret(),
        displaySmall = displaySmall.poiret(),
        headlineLarge = headlineLarge.poiret(),
        headlineMedium = headlineMedium.poiret(),
        headlineSmall = headlineSmall.poiret(),
        titleLarge = titleLarge.poiret(),
        titleMedium = titleMedium.josefin(FontWeight.SemiBold),
        titleSmall = titleSmall.josefin(FontWeight.SemiBold, 0.04),
        bodyLarge = bodyLarge.josefin(),
        bodyMedium = bodyMedium.josefin(),
        bodySmall = bodySmall.josefin(),
        labelLarge = labelLarge.josefin(FontWeight.SemiBold, 0.08),
        labelMedium = labelMedium.josefin(FontWeight.SemiBold, 0.08),
        labelSmall = labelSmall.josefin(FontWeight.SemiBold, 0.10),
    )
}

/** Poiret One marquee lettering at this style's size: for tabs and section headings (upper-case the text) */
fun TextStyle.marquee() = copy(fontFamily = Deco.Poiret, fontWeight = FontWeight.Normal, letterSpacing = Deco.MarqueeLetterSpacing)

/** Jost, the geometric face Deco Noir uses for numbers */
fun TextStyle.figures(weight: FontWeight = FontWeight.Light) = copy(fontFamily = Deco.Jost, fontWeight = weight, letterSpacing = 0.02.em)

/**
 * The Deco Noir card frame, drawn over the content: a gold hairline border, the faint 5px inner
 * band (ha-card-box-shadow inset) and stepped corner brackets top-left and bottom-right.
 */
fun Modifier.decoFrame(
    hairline: Color = Deco.Hair,
    brackets: Color = Deco.Gold,
    innerBand: Boolean = true,
): Modifier = drawWithContent {
    drawContent()
    drawDecoFrame(hairline, brackets, innerBand)
}

fun DrawScope.drawDecoFrame(hairline: Color = Deco.Hair, brackets: Color = Deco.Gold, innerBand: Boolean = true) {
    val hair = 1.dp.toPx()
    if (innerBand) {
        val band = 5.dp.toPx()
        drawRect(Deco.Gold.copy(alpha = 0.10f), topLeft = Offset(hair + band / 2, hair + band / 2),
            size = Size(size.width - 2 * hair - band, size.height - 2 * hair - band), style = Stroke(band))
    }
    drawRect(hairline, topLeft = Offset(hair / 2, hair / 2), size = Size(size.width - hair, size.height - hair), style = Stroke(hair))
    drawCornerBrackets(brackets)
}

/** Only the stepped corner brackets, for tiles whose picture is the frame */
fun DrawScope.drawCornerBrackets(color: Color = Deco.Gold, arm: Dp = Deco.BracketArm, thickness: Dp = Deco.BracketWidth) {
    val a = arm.toPx()
    val t = thickness.toPx()
    drawRect(color, Offset.Zero, Size(a, t))
    drawRect(color, Offset.Zero, Size(t, a))
    drawRect(color, Offset(size.width - a, size.height - t), Size(a, t))
    drawRect(color, Offset(size.width - t, size.height - a), Size(t, a))
}

/** The gold double rule under marquee headings (border-bottom: 3px double) */
@Composable
fun DecoDoubleRule(modifier: Modifier = Modifier, color: Color = Deco.Hair) {
    Box(
        modifier
            .fillMaxWidth()
            .height(3.dp)
            .drawBehind {
                val line = 1.dp.toPx()
                drawRect(color, Offset.Zero, Size(size.width, line))
                drawRect(color, Offset(0f, size.height - line), Size(size.width, line))
            },
    )
}

/**
 * The lovelace-background, painted rather than loaded: a midnight-to-ink wash, a warm glow at the
 * top, emerald and sapphire pools low on either side, a fan of gold rays with halo rings from the
 * top centre, fans along the bottom and pinstripes down both edges. Ported from
 * tools/make_sunburst.py, laid out for a 16:9 screen.
 */
fun Modifier.decoBackdrop(): Modifier = drawBehind {
    val w = size.width
    val h = size.height
    drawRect(Brush.verticalGradient(0f to Deco.Midnight, 0.55f to Deco.Ink))
    drawRect(Brush.radialGradient(listOf(Color(0xFF1D1A14), Color.Transparent), Offset(w / 2, -0.08f * h), radius = 0.42f * w))
    drawRect(Brush.radialGradient(listOf(Deco.Emerald.copy(alpha = 0.14f), Color.Transparent), Offset(0.92f * w, 0.78f * h), radius = 0.30f * w))
    drawRect(Brush.radialGradient(listOf(Deco.Sapphire.copy(alpha = 0.12f), Color.Transparent), Offset(0.04f * w, 0.62f * h), radius = 0.28f * w))

    val unit = w / 1600f // the SVG is drawn on a 1600-wide canvas
    val center = Offset(w / 2, -60 * unit)
    val rays = Brush.verticalGradient(0f to Deco.Gold.copy(alpha = 0.30f), 0.75f to Deco.Gold.copy(alpha = 0f), startY = 0f, endY = h)
    val stroke = 1.2f * unit.coerceAtLeast(1f)
    for (i in 0..40) {
        val a = PI * (0.05 + 0.90 * i / 40)
        val dx = cos(a).toFloat()
        val dy = sin(a).toFloat()
        drawLine(rays, center + Offset(dx, dy) * (320 * unit), center + Offset(dx, dy) * (2200 * unit), stroke)
    }
    for (r in listOf(310, 322, 540, 720)) {
        drawCircle(Deco.Gold.copy(alpha = 0.14f), r * unit, center, style = Stroke(1f))
    }
    val fan = Deco.Gold.copy(alpha = 0.10f)
    for (fx in listOf(200 * unit, w / 2, w - 200 * unit)) {
        for (r in 70..390 step 50) {
            drawArc(fan, 180f, 180f, false, Offset(fx - r * unit, h - r * unit), Size(2 * r * unit, 2 * r * unit), style = Stroke(1f))
        }
        for (k in 1..9) {
            val t = PI * k / 10
            drawLine(fan, Offset(fx, h), Offset(fx - cos(t).toFloat() * 390 * unit, h - sin(t).toFloat() * 390 * unit), 1f)
        }
    }
    val stripe = Deco.Gold.copy(alpha = 0.09f)
    for (x in listOf(70f, 86f, 1514f, 1530f)) {
        drawLine(stripe, Offset(x * unit, 0f), Offset(x * unit, h), 1f)
    }
}

/** A filled button: gold-hi with ink text when the remote is on it, otherwise a glass well with a gold hairline */
@Composable
fun DecoButton(
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    content: @Composable RowScope.() -> Unit,
) {
    val colors = MaterialTheme.colorScheme
    Button(
        onClick = onClick,
        modifier = modifier,
        enabled = enabled,
        shape = ButtonDefaults.shape(DecoButtonShape),
        colors = ButtonDefaults.colors(
            containerColor = Deco.Gold.copy(alpha = 0.22f),
            contentColor = Deco.GoldHi,
            focusedContainerColor = colors.inverseSurface,
            focusedContentColor = colors.inverseOnSurface,
            pressedContainerColor = Deco.Gold,
            pressedContentColor = Deco.Ink,
        ),
        border = ButtonDefaults.border(
            border = Border(BorderStroke(1.dp, Deco.Hair), shape = DecoButtonShape),
            focusedBorder = Border(BorderStroke(1.dp, Deco.GoldHi), shape = DecoButtonShape),
        ),
        contentPadding = DecoButtonPadding,
        content = content,
    )
}

/** A secondary button: a bare gold hairline, filled gold-hi when the remote is on it */
@Composable
fun DecoOutlinedButton(
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    content: @Composable RowScope.() -> Unit,
) {
    val colors = MaterialTheme.colorScheme
    OutlinedButton(
        onClick = onClick,
        modifier = modifier,
        enabled = enabled,
        shape = OutlinedButtonDefaults.shape(DecoButtonShape),
        colors = OutlinedButtonDefaults.colors(
            contentColor = Deco.Ivory,
            focusedContainerColor = colors.inverseSurface,
            focusedContentColor = colors.inverseOnSurface,
            pressedContainerColor = Deco.Gold,
            pressedContentColor = Deco.Ink,
        ),
        border = OutlinedButtonDefaults.border(
            border = Border(BorderStroke(1.dp, Deco.Hair), shape = DecoButtonShape),
            focusedBorder = Border(BorderStroke(1.dp, Deco.GoldHi), shape = DecoButtonShape),
            pressedBorder = Border(BorderStroke(1.dp, Deco.GoldHi), shape = DecoButtonShape),
        ),
        contentPadding = DecoButtonPadding,
        content = content,
    )
}

private val DecoButtonPadding = PaddingValues(horizontal = 20.dp, vertical = 10.dp)
