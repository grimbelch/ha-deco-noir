package com.evofactory.homeboard

import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.runtime.withFrameNanos
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.lifecycle.lifecycleScope
import androidx.tv.material3.MaterialTheme
import androidx.tv.material3.Surface
import androidx.tv.material3.SurfaceDefaults
import kotlinx.coroutines.launch

/**
 * Marquee's one screen: the lobby, scenes, weather, Jellyfin and Spotify (see MarqueeHome), under
 * a top bar with the network button and the settings cog. HomeBoard's tabs, cameras, Frigate
 * alerts, app row and Continue Watching are gone from the screen; their code is left in place.
 */
class MainActivity : ComponentActivity() {
    private val prefs by lazy { LauncherPrefs(this) }
    private var pingOpen by mutableStateOf(false)
    private var networkStatusOpen by mutableStateOf(false)
    private var haPicker by mutableStateOf<HaPick?>(null)
    private var haServer by mutableStateOf(HaServer(""))
    private var haEntities by mutableStateOf(emptyList<String>())
    private var haActions by mutableStateOf(emptyList<String>())
    private var launcherSettingsOpen by mutableStateOf(false)
    private var replaceHome by mutableStateOf(false)
    private var catchHomeKey by mutableStateOf(false)
    private var reopenAfterHome by mutableStateOf(false)
    private var showFreeMemory by mutableStateOf(false)
    private var exportOpen by mutableStateOf(false)
    private var importOpen by mutableStateOf(false)
    private var tab by mutableStateOf(MarqueeTab.Home)
    private var omega7 by mutableStateOf(Omega7Server())
    private var omega7Open by mutableStateOf(false)

    // Home override's crash guard: the launcher counts as started once it has stayed up a moment
    private val confirmStarted = Runnable {
        running = true
        if (prefs.overrideLaunches != 0) prefs.overrideLaunches = 0
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        haServer = HaServer(prefs.haUrl, prefs.haToken, prefs.haRefreshToken)
        haEntities = prefs.haEntities
        haActions = prefs.haActions
        omega7 = prefs.omega7
        setContent {
            MaterialTheme(colorScheme = AppColorScheme, shapes = DecoShapes, typography = DecoTypography) {
                Surface(
                    modifier = Modifier.fillMaxSize().decoBackdrop(),
                    colors = SurfaceDefaults.colors(containerColor = Color.Transparent),
                ) {
                    val scenesFocus = remember { FocusRequester() }
                    val jellyfinFocus = remember { FocusRequester() }
                    val jellyfinSelected = remember { mutableStateOf(false) }
                    // The marquee is the star: it has the selection from the start (MarqueeHome). Back goes
                    // to the Home page, and on Home to the marquee.
                    BackHandler {
                        if (tab != MarqueeTab.Home) tab = MarqueeTab.Home else runCatching { jellyfinFocus.requestFocus() }
                    }

                    val actions = haActions.take(MAX_HA_ACTIONS)
                    // A picked weather wins; otherwise the dashboard's own
                    val weatherId = haEntities.firstOrNull(::isHaWeather) ?: DEFAULT_WEATHER_ENTITY
                    val followed = remember(haEntities, actions, weatherId) {
                        (haEntities + actions + weatherId + SPOTIFY_ENTITY + BasementLights.map { it.first } + DownloadSensors.map { it.first }).distinct()
                    }
                    val haConnection = rememberHaConnection(haServer, followed)

                    Column(modifier = Modifier.fillMaxSize()) {
                        MarqueeTopBar(
                            tab = tab,
                            onTabChange = { tab = it },
                            showFreeMemory = showFreeMemory,
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(start = EdgePadding, top = TopPadding, end = EdgePadding),
                            actions = {
                                HomeHelperWarning(
                                    replaceHome,
                                    onClick = { launcherSettingsOpen = true },
                                    modifier = Modifier.weight(1f, fill = false),
                                )
                                NetworkButton(onClick = { networkStatusOpen = true })
                            },
                        ) {
                            SettingsButton(
                                homeAssistantSet = haServer.isSet,
                                onOpenHomeAssistant = { haPicker = it },
                                onLogOutOfHomeAssistant = ::logOutOfHa,
                                onOpenPing = { pingOpen = true },
                                onOpenOmega7 = { omega7Open = true },
                                onOpenLauncherSettings = { launcherSettingsOpen = true },
                            )
                        }
                        val page = Modifier
                            .weight(1f)
                            .fillMaxWidth()
                            .padding(start = EdgePadding, top = 20.dp, end = EdgePadding, bottom = EdgePadding)
                        val ha = if (haServer.isSet) haConnection else null
                        when (tab) {
                            MarqueeTab.Home -> MarqueeHome(
                                haConnection = ha,
                                haServer = haServer,
                                entityIds = haEntities,
                                actionIds = actions,
                                weatherId = weatherId,
                                scenesFocus = scenesFocus,
                                jellyfinFocus = jellyfinFocus,
                                jellyfinSelected = jellyfinSelected,
                                onSetUpHa = { haPicker = HaPick.Sensors },
                                modifier = page,
                            )
                            MarqueeTab.Media -> MediaPage(ha, page)
                            MarqueeTab.Omega7 -> Omega7Page(
                                server = omega7,
                                onSetUp = { omega7Open = true },
                                onLoginRejected = { saveOmega7(Omega7Server(omega7.url)) },
                                modifier = page,
                            )
                        }
                    }
                    if (omega7Open) {
                        Omega7Dialog(initial = omega7, onSave = ::saveOmega7, onDismiss = { omega7Open = false })
                    }
                    haPicker?.let { pick ->
                        HomeAssistantDialog(
                            pick = pick,
                            initialServer = haServer,
                            initialUsername = remember { prefs.haUsername },
                            initialEntities = if (pick == HaPick.Actions) haActions else haEntities,
                            loginRejected = haConnection.status == HaStatus.TokenRejected,
                            onSave = { server, username, entities ->
                                // A replaced username-and-password login is ended in Home Assistant
                                if (haServer.refreshToken != server.refreshToken) revokeHaLogin(haServer)
                                haServer = server
                                prefs.haUrl = server.url
                                prefs.haToken = server.token
                                prefs.haRefreshToken = server.refreshToken
                                prefs.haUsername = username
                                if (pick == HaPick.Actions) {
                                    haActions = entities
                                    prefs.haActions = entities
                                } else {
                                    haEntities = entities
                                    prefs.haEntities = entities
                                }
                            },
                            onDiscardLogin = ::revokeHaLogin,
                            onDismiss = { haPicker = null },
                        )
                    }
                    if (launcherSettingsOpen) {
                        LauncherSettingsDialog(
                            catchHomeKey = catchHomeKey,
                            reopenAfterHome = reopenAfterHome,
                            autoTurnedOff = remember { prefs.replaceHomeAutoOff },
                            onCatchHomeKeyChange = { on ->
                                prefs.catchHomeKey = on
                                homeOverrideChanged()
                            },
                            onReopenAfterHomeChange = { on ->
                                prefs.reopenAfterHome = on
                                homeOverrideChanged()
                            },
                            showFreeMemory = showFreeMemory,
                            onShowFreeMemoryChange = { on ->
                                prefs.showFreeMemory = on
                                showFreeMemory = on
                            },
                            onExport = { exportOpen = true },
                            onImport = { importOpen = true },
                            onDismiss = { launcherSettingsOpen = false },
                        )
                    }
                    if (exportOpen) {
                        ExportDialog(
                            file = SettingsFile(
                                login = haServer.takeIf { it.isSet },
                                username = remember { prefs.haUsername },
                                sensors = haEntities.map { NamedEntity(it, haConnection.entities[it]?.name ?: it) },
                                actions = haActions.map { NamedEntity(it, haConnection.entities[it]?.name ?: it) },
                            ),
                            onDismiss = { exportOpen = false },
                        )
                    }
                    if (importOpen) {
                        ImportDialog(onImport = ::applyImport, onDismiss = { importOpen = false })
                    }
                    if (networkStatusOpen) {
                        NetworkStatusDialog(
                            frigate = null,
                            onOpenPing = { pingOpen = true },
                            onDismiss = { networkStatusOpen = false },
                        )
                    }
                    if (pingOpen) {
                        PingDialog(
                            initialHost = remember { prefs.pingHost },
                            onHostEntered = { prefs.pingHost = it },
                            onDismiss = { pingOpen = false },
                        )
                    }
                }
            }
        }
    }

    private fun saveOmega7(value: Omega7Server) {
        omega7 = value
        prefs.omega7 = value
    }

    /** Ends the login; the address, username and chosen entities stay for logging in again */
    private fun logOutOfHa() {
        revokeHaLogin(haServer)
        haServer = HaServer(haServer.url)
        prefs.haToken = ""
        prefs.haRefreshToken = ""
    }

    private fun revokeHaLogin(server: HaServer) {
        lifecycleScope.launch { haRevoke(server) }
    }

    /** Adds the Home Assistant login, sensors and scenes in the file; cameras, Frigate and app tiles no longer apply */
    private fun applyImport(file: SettingsFile) {
        file.login?.let { server ->
            // A replaced username-and-password login is ended in Home Assistant
            if (haServer.refreshToken != server.refreshToken) revokeHaLogin(haServer)
            haServer = server
            prefs.haUrl = server.url
            prefs.haToken = server.token
            prefs.haRefreshToken = server.refreshToken
            prefs.haUsername = file.username
        }
        haEntities = (haEntities + file.sensors.map { it.id }).distinct()
        prefs.haEntities = haEntities
        haActions = (haActions + file.actions.map { it.id }).distinct()
        prefs.haActions = haActions
        Toast.makeText(this, "Settings imported", Toast.LENGTH_SHORT).show()
    }

    private fun homeOverrideChanged() {
        prefs.replaceHomeAutoOff = false
        updateReplaceHome()
    }

    private fun updateReplaceHome() {
        replaceHome = prefs.replaceHome
        catchHomeKey = prefs.catchHomeKey
        reopenAfterHome = prefs.reopenAfterHome
        showFreeMemory = prefs.showFreeMemory
    }

    override fun onResume() {
        super.onResume()
        // The home override may have switched itself off meanwhile
        updateReplaceHome()
        window.decorView.postDelayed(confirmStarted, 2_000)
    }

    override fun onPause() {
        super.onPause()
        window.decorView.removeCallbacks(confirmStarted)
    }

    override fun onDestroy() {
        super.onDestroy()
        running = false
    }

    companion object {
        /** Started properly and still alive; a crash takes the whole process, so this resets */
        @Volatile
        var running = false
            private set
    }
}
