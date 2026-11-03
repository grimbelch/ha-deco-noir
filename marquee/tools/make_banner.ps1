# Draws Marquee's launcher banner (res/drawable-xhdpi/banner.png, 320x180) in Deco Noir:
# ink ground, gold sunburst from the top centre, a hairline frame with stepped corner brackets,
# and MARQUEE in Poiret One between two diamonds.
#   powershell -ExecutionPolicy Bypass -File tools\make_banner.ps1
Add-Type -AssemblyName System.Drawing
$root = Split-Path -Parent $PSScriptRoot
$out = Join-Path $root 'app\src\main\res\drawable-xhdpi\banner.png'
$fontFile = Join-Path $root 'app\src\main\res\font\deco_poiret.ttf'

$scale = 4 # drawn large, then scaled down for clean hairlines
$W = 320 * $scale; $H = 180 * $scale
$bmp = New-Object System.Drawing.Bitmap $W, $H
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = 'AntiAlias'
$g.TextRenderingHint = 'AntiAliasGridFit'

function C($a, $r, $gr, $b) { [System.Drawing.Color]::FromArgb($a, $r, $gr, $b) }
$ink = C 255 11 11 14; $midnight = C 255 17 19 28
$gold = C 255 201 164 76; $goldHi = C 255 230 207 154

# Ground: midnight to ink
$rect = New-Object System.Drawing.Rectangle 0, 0, $W, $H
$wash = New-Object System.Drawing.Drawing2D.LinearGradientBrush $rect, $midnight, $ink, 90
$g.FillRectangle($wash, $rect)

# Sunburst: rays from just above the top centre, fading downwards
$cx = $W / 2; $cy = -0.10 * $H
for ($i = 0; $i -le 28; $i++) {
    $a = [Math]::PI * (0.04 + 0.92 * $i / 28)
    $x1 = $cx + [Math]::Cos($a) * 0.16 * $W; $y1 = $cy + [Math]::Sin($a) * 0.16 * $W
    $x2 = $cx + [Math]::Cos($a) * 1.2 * $W;  $y2 = $cy + [Math]::Sin($a) * 1.2 * $W
    $p1 = New-Object System.Drawing.PointF $x1, $y1; $p2 = New-Object System.Drawing.PointF $x2, $y2
    $ray = New-Object System.Drawing.Drawing2D.LinearGradientBrush $p1, $p2, (C 90 201 164 76), (C 0 201 164 76)
    $g.DrawLine((New-Object System.Drawing.Pen $ray, (1.2 * $scale)), $p1, $p2)
}
foreach ($r in 0.15, 0.158, 0.27) {
    $rr = $r * $W
    $g.DrawEllipse((New-Object System.Drawing.Pen (C 50 201 164 76), $scale), [float]($cx - $rr), [float]($cy - $rr), [float](2 * $rr), [float](2 * $rr))
}

# Frame: hairline, faint inner band, stepped corner brackets
$m = 10 * $scale
$g.DrawRectangle((New-Object System.Drawing.Pen (C 97 201 164 76), $scale), $m, $m, $W - 2 * $m, $H - 2 * $m)
$band = 5 * $scale
$g.DrawRectangle((New-Object System.Drawing.Pen (C 26 201 164 76), $band), [float]($m + $band / 2 + $scale), [float]($m + $band / 2 + $scale), [float]($W - 2 * $m - $band - 2 * $scale), [float]($H - 2 * $m - $band - 2 * $scale))
$arm = 22 * $scale; $t = 2 * $scale
$goldBrush = New-Object System.Drawing.SolidBrush $gold
$g.FillRectangle($goldBrush, $m, $m, $arm, $t); $g.FillRectangle($goldBrush, $m, $m, $t, $arm)
$g.FillRectangle($goldBrush, $W - $m - $arm, $H - $m - $t, $arm, $t); $g.FillRectangle($goldBrush, $W - $m - $t, $H - $m - $arm, $t, $arm)

# Title: MARQUEE in Poiret One, letter-spaced by hand
$fonts = New-Object System.Drawing.Text.PrivateFontCollection
$fonts.AddFontFile($fontFile)
$font = New-Object System.Drawing.Font $fonts.Families[0], (40 * $scale), ([System.Drawing.FontStyle]::Regular), ([System.Drawing.GraphicsUnit]::Pixel)
$word = 'MARQUEE'; $spacing = 5 * $scale
$fmt = [System.Drawing.StringFormat]::GenericTypographic
$widths = @(); foreach ($ch in $word.ToCharArray()) { $widths += $g.MeasureString([string]$ch, $font, 10000, $fmt).Width }
$total = ($widths | Measure-Object -Sum).Sum + $spacing * ($word.Length - 1)
$height = $g.MeasureString($word, $font, 10000, $fmt).Height
$x = ($W - $total) / 2; $y = ($H - $height) / 2 + 4 * $scale
$textBrush = New-Object System.Drawing.SolidBrush $goldHi
for ($k = 0; $k -lt $word.Length; $k++) {
    $g.DrawString([string]$word[$k], $font, $textBrush, [float]$x, [float]$y, $fmt)
    $x += $widths[$k] + $spacing
}

# Double rule under the title, broken by a diamond at either end
$ruleY = $y + $height + 6 * $scale
$left = ($W - $total) / 2; $right = $left + $total
$rulePen = New-Object System.Drawing.Pen (C 140 201 164 76), $scale
$g.DrawLine($rulePen, [float]($left + 12 * $scale), [float]$ruleY, [float]($right - 12 * $scale), [float]$ruleY)
$g.DrawLine($rulePen, [float]($left + 12 * $scale), [float]($ruleY + 3 * $scale), [float]($right - 12 * $scale), [float]($ruleY + 3 * $scale))
foreach ($dx in ($left + 4 * $scale), ($right - 4 * $scale)) {
    $d = 4 * $scale; $dy = $ruleY + 1.5 * $scale
    $pts = [System.Drawing.PointF[]]@(
        (New-Object System.Drawing.PointF $dx, ($dy - $d)), (New-Object System.Drawing.PointF ($dx + $d), $dy),
        (New-Object System.Drawing.PointF $dx, ($dy + $d)), (New-Object System.Drawing.PointF ($dx - $d), $dy))
    $g.FillPolygon($goldBrush, $pts)
}

# Down to 320x180
$small = New-Object System.Drawing.Bitmap 320, 180
$gs = [System.Drawing.Graphics]::FromImage($small)
$gs.InterpolationMode = 'HighQualityBicubic'
$gs.DrawImage($bmp, 0, 0, 320, 180)
$small.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)
$gs.Dispose(); $small.Dispose(); $g.Dispose(); $bmp.Dispose(); $fonts.Dispose()
Write-Output "Wrote $out"
