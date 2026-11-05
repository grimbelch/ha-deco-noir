package com.evofactory.homeboard

import android.net.ConnectivityManager
import android.net.LinkProperties
import android.net.Network
import android.net.NetworkCapabilities
import android.net.RouteInfo
import android.os.Build
import android.os.Handler
import java.util.WeakHashMap

/*
 * Marquee runs on Android 7.1 (API 25) for Fire OS 6 (Fire TV Stick 4K, 2018), where HomeBoard
 * needs Android 9. These fill in the few platform calls that came later.
 */

/** The callbacks registered below API 26, keyed by the caller's, so they can be unregistered */
private val forwarders = WeakHashMap<ConnectivityManager.NetworkCallback, ConnectivityManager.NetworkCallback>()

/**
 * registerDefaultNetworkCallback with callbacks on [handler]. Before API 26 there's no Handler
 * overload, so the callbacks are forwarded to [handler] from Android's own thread.
 */
fun ConnectivityManager.registerDefaultNetworkCallbackOn(callback: ConnectivityManager.NetworkCallback, handler: Handler) {
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
        registerDefaultNetworkCallback(callback, handler)
        return
    }
    val forwarder = object : ConnectivityManager.NetworkCallback() {
        override fun onAvailable(network: Network) { handler.post { callback.onAvailable(network) } }
        override fun onLosing(network: Network, maxMsToLive: Int) { handler.post { callback.onLosing(network, maxMsToLive) } }
        override fun onLost(network: Network) { handler.post { callback.onLost(network) } }
        override fun onCapabilitiesChanged(network: Network, capabilities: NetworkCapabilities) {
            handler.post { callback.onCapabilitiesChanged(network, capabilities) }
        }
        override fun onLinkPropertiesChanged(network: Network, linkProperties: LinkProperties) {
            handler.post { callback.onLinkPropertiesChanged(network, linkProperties) }
        }
    }
    synchronized(forwarders) { forwarders[callback] = forwarder }
    registerDefaultNetworkCallback(forwarder)
}

/** Unregisters a callback registered with [registerDefaultNetworkCallbackOn] */
fun ConnectivityManager.unregisterNetworkCallbackCompat(callback: ConnectivityManager.NetworkCallback) {
    val forwarder = synchronized(forwarders) { forwarders.remove(callback) }
    unregisterNetworkCallback(forwarder ?: callback)
}

/** RouteInfo.hasGateway() is API 29; before that a route without a gateway has 0.0.0.0 or :: */
fun RouteInfo.hasGatewayCompat(): Boolean =
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) hasGateway() else gateway?.isAnyLocalAddress == false
