package com.evofactory.homeboard

import androidx.compose.ui.graphics.Color
import androidx.tv.material3.darkColorScheme

/**
 * The launcher's colors: Deco Noir (see DecoKit.kt). The library's components read these too, so
 * screens use the scheme rather than their own colors:
 * - surfaceVariant: panels, dialogs and inactive buttons (smoked glass)
 * - onSurface: text (ivory)
 * - onSurfaceVariant: secondary text and the text of inactive buttons (dimmed ivory)
 * - inverseSurface / inverseOnSurface: the fill and text of the item the remote is on (gold-hi on ink)
 * - border: the outline of the item the remote is on (gold)
 */
val AppColorScheme = darkColorScheme(
    primary = Deco.Gold,
    onPrimary = Deco.Ink,
    secondary = Deco.Sapphire,
    tertiary = Deco.Emerald,
    background = Deco.Ink,
    onBackground = Deco.Ivory,
    surface = Deco.Ink,
    onSurface = Deco.Ivory,
    surfaceVariant = Deco.Glass,
    onSurfaceVariant = Deco.IvoryDim,
    inverseSurface = Deco.GoldHi,
    inverseOnSurface = Deco.Ink,
    error = Deco.Garnet,
    onError = Deco.Ink,
    border = Deco.Gold,
    borderVariant = Deco.Hair,
)

/** A step above surfaceVariant: menus over panels, and buttons on dialogs */
val RaisedSurface = Deco.Raised

/** A step below onSurfaceVariant: figures that are only there if you look for them */
val FaintText: Color = Deco.IvoryFaint
