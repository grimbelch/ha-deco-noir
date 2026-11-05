package com.evofactory.homeboard

import android.content.Context
import android.media.AudioAttributes
import android.media.AudioFocusRequest
import android.media.AudioManager
import android.media.MediaPlayer
import android.os.Build
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withContext
import java.io.File
import kotlin.coroutines.resume

/**
 * Plays Omega-7's spoken replies on the TV, one after another, the way its web remote does in a
 * browser. Anything else playing (Spotify) ducks while it speaks.
 */
class Omega7Voice(private val context: Context) {
    private val audio = context.getSystemService(AudioManager::class.java)
    private val attributes = AudioAttributes.Builder()
        .setUsage(AudioAttributes.USAGE_ASSISTANT)
        .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
        .build()

    /** Plays one WAV clip to its end; cancelling stops it */
    suspend fun play(wav: ByteArray) {
        val file = withContext(Dispatchers.IO) {
            File(context.cacheDir, "omega7_speech.wav").apply { writeBytes(wav) }
        }
        val release = requestDuck()
        val player = MediaPlayer()
        try {
            player.setAudioAttributes(attributes)
            player.setDataSource(file.path)
            withContext(Dispatchers.IO) { player.prepare() }
            suspendCancellableCoroutine { done ->
                player.setOnCompletionListener { if (done.isActive) done.resume(Unit) }
                player.setOnErrorListener { _, _, _ ->
                    if (done.isActive) done.resume(Unit)
                    true
                }
                done.invokeOnCancellation { runCatching { player.stop() } }
                player.start()
            }
        } catch (e: Exception) {
            if (e is kotlinx.coroutines.CancellationException) throw e
            AppLog.w("Omega7Voice", "Couldn't play a reply", e)
        } finally {
            player.release()
            release()
        }
    }

    /** Asks the others to duck; returns how to give the sound back */
    @Suppress("DEPRECATION")
    private fun requestDuck(): () -> Unit {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val request = AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK)
                .setAudioAttributes(attributes)
                .build()
            audio.requestAudioFocus(request)
            return { audio.abandonAudioFocusRequest(request) }
        }
        val listener = AudioManager.OnAudioFocusChangeListener { }
        audio.requestAudioFocus(listener, AudioManager.STREAM_MUSIC, AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK)
        return { audio.abandonAudioFocus(listener) }
    }
}
