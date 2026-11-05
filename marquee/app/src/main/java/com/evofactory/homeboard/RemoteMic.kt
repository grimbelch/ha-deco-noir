package com.evofactory.homeboard

import android.annotation.SuppressLint
import android.content.Context
import android.media.AudioDeviceInfo
import android.media.AudioFormat
import android.media.AudioManager
import android.media.AudioRecord
import android.media.MediaRecorder
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.isActive
import kotlinx.coroutines.withContext
import java.io.ByteArrayOutputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.math.sqrt

/**
 * Records speech for Omega-7 from the TV's microphone: on a Fire TV, the voice remote's (it shows
 * up as Amazon's Bluetooth LE mic input). 16 kHz mono, as WAV.
 */
class RemoteMic(private val context: Context) {
    /** The inputs Android offers, for the log: which one is the remote */
    fun describeInputs(): String = context.getSystemService(AudioManager::class.java)
        .getDevices(AudioManager.GET_DEVICES_INPUTS)
        .joinToString { "${it.productName} (type ${it.type}, id ${it.id})" }

    /**
     * Records until [keepGoing] says stop or [maxMs] pass, telling [onLevel] how loud each slice
     * is (0 to 1). Returns the WAV, or null if Android gave no microphone.
     */
    @SuppressLint("MissingPermission") // asked for by the page before calling
    suspend fun record(maxMs: Long, keepGoing: () -> Boolean, onLevel: (Float) -> Unit): ByteArray? = withContext(Dispatchers.IO) {
        val minBuffer = AudioRecord.getMinBufferSize(RATE, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT)
        if (minBuffer <= 0) return@withContext null
        val recorder = AudioRecord(
            MediaRecorder.AudioSource.VOICE_RECOGNITION, RATE,
            AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT, minBuffer * 4,
        )
        if (recorder.state != AudioRecord.STATE_INITIALIZED) {
            recorder.release()
            return@withContext null
        }
        remoteInput()?.let { recorder.preferredDevice = it }
        val pcm = ByteArrayOutputStream()
        val chunk = ShortArray(minBuffer / 2)
        val bytes = ByteBuffer.allocate(chunk.size * 2).order(ByteOrder.LITTLE_ENDIAN)
        val started = System.currentTimeMillis()
        try {
            recorder.startRecording()
            AppLog.i(TAG, "Recording from ${recorder.routedDevice?.productName ?: "default input"}; inputs: ${describeInputs()}")
            while (isActive && keepGoing() && System.currentTimeMillis() - started < maxMs) {
                val read = recorder.read(chunk, 0, chunk.size)
                if (read <= 0) continue
                var sum = 0.0
                bytes.clear()
                for (i in 0 until read) {
                    sum += chunk[i].toDouble() * chunk[i]
                    bytes.putShort(chunk[i])
                }
                pcm.write(bytes.array(), 0, read * 2)
                onLevel((sqrt(sum / read) / LOUD).toFloat().coerceIn(0f, 1f))
            }
        } finally {
            runCatching { recorder.stop() }
            recorder.release()
        }
        wav(pcm.toByteArray())
    }

    /** The voice remote's mic if Android lists it: not the HDMI or USB inputs */
    private fun remoteInput(): AudioDeviceInfo? = context.getSystemService(AudioManager::class.java)
        .getDevices(AudioManager.GET_DEVICES_INPUTS)
        .firstOrNull { device ->
            val name = device.productName?.toString().orEmpty()
            name.contains("remote", ignoreCase = true) || name.contains("BLE", ignoreCase = true)
        }

    private fun wav(pcm: ByteArray): ByteArray {
        val header = ByteBuffer.allocate(44).order(ByteOrder.LITTLE_ENDIAN).apply {
            put("RIFF".toByteArray()); putInt(36 + pcm.size); put("WAVE".toByteArray())
            put("fmt ".toByteArray()); putInt(16); putShort(1); putShort(1)
            putInt(RATE); putInt(RATE * 2); putShort(2); putShort(16)
            put("data".toByteArray()); putInt(pcm.size)
        }
        return header.array() + pcm
    }

    companion object {
        private const val TAG = "RemoteMic"
        private const val RATE = 16_000

        // An RMS this high fills the level meter
        private const val LOUD = 6_000.0
    }
}
