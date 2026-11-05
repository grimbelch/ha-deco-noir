package com.evofactory.homeboard

import android.graphics.BitmapFactory
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.isActive
import kotlinx.coroutines.withContext
import okhttp3.FormBody
import okhttp3.HttpUrl.Companion.toHttpUrlOrNull
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.IOException
import java.net.SocketException
import java.net.SocketTimeoutException
import java.net.UnknownHostException
import java.security.SecureRandom
import java.util.concurrent.TimeUnit
import javax.net.ssl.SSLException

/*
 * Omega-7, the servo-skull (github.com/grimbelch/servoskull), through its web remote: an HTTPS
 * server with a self-signed certificate on port 8080. Logging in takes the 4-digit access code the
 * skull shows on its eye when asked ("show the web access code"); that gives a session key, sent
 * as "Authorization: Bearer <key>" from then on (the web remote allows that for scripts).
 */

private const val OMEGA7_PORT = 8080
private const val SESSION_COOKIE = "omega7_session"

/** Where Omega-7 is and the login the TV holds. [certPin]: the certificate seen when logging in. */
data class Omega7Server(val url: String = "", val key: String = "", val certPin: String = "") {
    val isSet get() = url.isNotEmpty() && key.isNotEmpty()
}

/** "192.168.1.40" or "omega7" → "https://192.168.1.40:8080". Null if invalid. */
fun normalizeOmega7Url(input: String): String? {
    val text = input.trim()
    if (text.isEmpty()) return null
    val withScheme = when {
        "://" in text -> text
        ':' in text -> "https://$text"
        else -> "https://${text.trimEnd('/')}:$OMEGA7_PORT"
    }
    val url = withScheme.toHttpUrlOrNull() ?: return null
    return url.newBuilder().encodedPath("/").query(null).fragment(null).build().toString().trimEnd('/')
}

class Omega7Exception(message: String, val loginRejected: Boolean = false) : Exception(message)

/** One line of what was said, as the web remote's vox log keeps it */
data class VoxLine(val time: String, val speaker: String, val text: String)

/** The parts of /api/state the TV shows */
class Omega7State(json: JSONObject) {
    val name: String = json.optString("skull_name").ifEmpty { "Omega-7" }
    val mood: String = json.optString("mood")
    val master: String = json.optString("master")
    val silent: Boolean = json.optString("silent_mode") == "ACTIVE"
    val temperature: String = json.optString("temperature")
    val power: String = json.opt("power")?.let(::describe).orEmpty()
    val cpu: String = json.opt("cpu")?.let(::describe).orEmpty()
    val ram: String = listOfNotNull(json.opt("ram")?.let(::describe), json.opt("ram_total")?.let(::describe)).joinToString(" / ")
    val storage: String = listOfNotNull(json.opt("storage")?.let(::describe), json.opt("storage_total")?.let(::describe)).joinToString(" / ")
    val game: String = json.optString("active_game").takeUnless { it.isEmpty() || it == "None" } ?: "None"
    val screensavers: List<String> = json.optJSONArray("screensavers")?.let { a -> (0 until a.length()).map { a.optString(it) } }.orEmpty()
    val vox: List<VoxLine> = json.optJSONArray("vox_logs")?.let { a ->
        (0 until a.length()).mapNotNull { a.optJSONObject(it) }.map { VoxLine(it.optString("time"), it.optString("speaker"), it.optString("text")) }
    }.orEmpty()

    /** Clips of its speech, newest last; the ids are times in milliseconds */
    val audioIds: List<Long> = json.optJSONArray("audio_ids")?.let { a -> (0 until a.length()).map { a.optLong(it) } }
        ?: listOfNotNull(json.optLong("audio_id").takeIf { it > 0 })

    private fun describe(value: Any): String? = when (value) {
        JSONObject.NULL -> null
        is JSONObject -> value.optString("summary").ifEmpty { value.optString("status") }.ifEmpty { null }
        is Double -> "%.0f".format(value)
        else -> value.toString().ifEmpty { null }
    }
}

/** Talks to one Omega-7 */
class Omega7Client(private val server: Omega7Server) {
    private val trust = PinningTrustManager(server.certPin)

    /** The certificate of the last connection, to save as [Omega7Server.certPin] */
    val seenCertPin: String get() = trust.seen

    private val http: OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(5, TimeUnit.SECONDS)
        .readTimeout(10, TimeUnit.SECONDS)
        .sslSocketFactory(frigateSslContext().apply { init(null, arrayOf(trust), SecureRandom()) }.socketFactory, trust)
        // A self-signed certificate rarely names the address it's reached at: the pin identifies it
        .hostnameVerifier { _, _ -> true }
        // The login answers with a redirect carrying the session cookie: read it, don't follow it
        .followRedirects(false)
        .addInterceptor { chain ->
            val request = chain.request()
            chain.proceed(if (server.key.isEmpty()) request else request.newBuilder().header("Authorization", "Bearer ${server.key}").build())
        }
        .build()

    /** Logs in with the access code shown on the eye; returns the session key */
    suspend fun logIn(code: String): String = call(Request.Builder()
        .url("${server.url}/login")
        .post(FormBody.Builder().add("code", code.trim()).add("next", "/").build())
        .build()) { response ->
        val key = response.headers("Set-Cookie")
            .firstOrNull { it.startsWith("$SESSION_COOKIE=") }
            ?.substringBefore(';')?.substringAfter('=')
            ?.takeIf { it.isNotEmpty() }
        when {
            key != null -> key
            response.code == 429 -> throw Omega7Exception("Too many attempts: wait a few minutes")
            else -> throw Omega7Exception("Omega-7 refused the code. Ask it to show the web access code again.")
        }
    }

    suspend fun state(): Omega7State = call(Request.Builder().url("${server.url}/api/state").build()) { response ->
        checkOk(response.code)
        Omega7State(JSONObject(response.body.string()))
    }

    /** One clip of what it said, as WAV */
    suspend fun speech(id: Long): ByteArray = call(Request.Builder().url("${server.url}/api/last_speech.wav?id=$id").build()) { response ->
        checkOk(response.code)
        response.body.bytes()
    }

    /** As if said to it: queued like a spoken request */
    suspend fun command(text: String) = post("/api/command", JSONObject().put("command", text))

    /** Wakes it to listen */
    suspend fun wake() = post("/api/wake", JSONObject())

    /** Runs one of its screensavers on the eye for a while */
    suspend fun screensaver(name: String) = post("/api/screensaver", JSONObject().put("animation", name))

    private suspend fun post(path: String, body: JSONObject) {
        call(Request.Builder().url(server.url + path).post(body.toString().toRequestBody("application/json".toMediaType())).build()) {
            checkOk(it.code)
        }
    }

    /**
     * The eye as Omega-7 draws it: [onFrame] gets each frame of the MJPEG stream, at most every
     * [minFrameMs] (decoding every frame would keep a TV stick busy). Runs until cancelled or the
     * stream breaks; throws [Omega7Exception] then.
     */
    suspend fun watchEye(minFrameMs: Long = 66, onFrame: (ImageBitmap) -> Unit) {
        val job = currentCoroutineContext()[Job]
        val streaming = http.newBuilder().readTimeout(0, TimeUnit.MILLISECONDS).build()
        val call = streaming.newCall(Request.Builder().url("${server.url}/api/ocular_stream.mjpeg").build())
        // Leaving the page cancels the coroutine; that has to unblock the read too
        val cancelOnLeave = job?.invokeOnCompletion { call.cancel() }
        try {
            withContext(Dispatchers.IO) {
                call.execute().use { response ->
                    checkOk(response.code)
                    val source = response.body.source()
                    var last = 0L
                    while (isActive) {
                        // Part headers, up to the blank line; the length says how much JPEG follows
                        var length = -1
                        while (true) {
                            val line = source.readUtf8LineStrict()
                            if (line.isEmpty() && length >= 0) break
                            if (line.startsWith("Content-Length:", ignoreCase = true)) length = line.substringAfter(':').trim().toIntOrNull() ?: -1
                        }
                        val now = System.currentTimeMillis()
                        if (now - last < minFrameMs) {
                            source.skip(length.toLong())
                            continue
                        }
                        val bytes = source.readByteArray(length.toLong())
                        BitmapFactory.decodeByteArray(bytes, 0, bytes.size)?.let { onFrame(it.asImageBitmap()) }
                        last = now
                    }
                }
            }
        } catch (e: IOException) {
            if (job?.isActive == false) return
            throw Omega7Exception("The eye's stream stopped: ${e.message ?: e.javaClass.simpleName}")
        } finally {
            cancelOnLeave?.dispose()
        }
    }

    private fun checkOk(code: Int) {
        when {
            code == 401 -> throw Omega7Exception("Omega-7 ended the TV's login: connect again in Settings › Omega-7", loginRejected = true)
            code !in 200..299 -> throw Omega7Exception("Omega-7 answered HTTP $code")
        }
    }

    private suspend fun <T> call(request: Request, read: (okhttp3.Response) -> T): T =
        withContext(Dispatchers.IO) {
            try {
                http.newCall(request).execute().use(read)
            } catch (e: IOException) {
                throw Omega7Exception(
                    when {
                        trust.changed -> "Omega-7's certificate changed. Connect again in Settings › Omega-7 to accept it."
                        e is UnknownHostException -> "Unknown address: ${server.url}"
                        e is SocketException || e is SocketTimeoutException -> "Can't reach Omega-7 at ${server.url}"
                        e is SSLException -> "HTTPS problem: ${e.message}"
                        else -> "Problem with Omega-7: ${e.message ?: e.javaClass.simpleName}"
                    },
                )
            }
        }
}
