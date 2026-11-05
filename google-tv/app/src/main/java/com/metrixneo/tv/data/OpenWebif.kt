package com.metrixneo.tv.data

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.InetAddress
import java.net.URL
import java.net.URLEncoder
import java.util.Base64
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.text.Html

data class Channel(
    val name: String,
    val ref: String,
    val bouquet: String = "TV",
    val current: String = "",
    val next: String = ""
)

data class ReceiverSettings(val host: String = "192.168.11.2", val port: Int = 80,
    val username: String = "", val password: String = "")

data class Programme(val title: String, val description: String, val begin: Long, val duration: Long) {
    fun progress(now: Long = System.currentTimeMillis() / 1000): Float =
        if (duration > 0) ((now - begin).toFloat() / duration).coerceIn(0f, 1f) else 0f
}
data class Satellite(val name: String, val ref: String)
fun isDirectoryRef(ref: String): Boolean = ((ref.split(':').getOrNull(1)?.toIntOrNull() ?: 0) and (1 or 128)) != 0
data class ServiceEntry(val name: String, val ref: String, val directory: Boolean)

/** OpenWebif read-only API: no zap, timer, plugin or settings changes. */
class OpenWebif(private val settings: ReceiverSettings) {
    private val streamUrls = StreamUrlCache()
    fun cachedStream(channel: Channel): String? = streamUrls.get(channel.ref)
    fun invalidateStream(channel: Channel) { streamUrls.remove(channel.ref) }
    private fun validateHost(host: String) {
        require(settings.port in 1..65535) { "Port invalide" }
        require(Regex("[a-zA-Z0-9.-]{1,253}").matches(host)) { "Adresse invalide" }
        val address = InetAddress.getByName(host)
        require(address.isSiteLocalAddress || address.isLoopbackAddress || address.isLinkLocalAddress) {
            "Seules les adresses privées du réseau local sont autorisées"
        }
    }
    private fun request(path: String): String {
        validateHost(settings.host)
        val conn = URL("http://" + settings.host + ":" + settings.port + path).openConnection() as HttpURLConnection
        conn.connectTimeout = 4500
        conn.readTimeout = 8000
        if (settings.username.isNotBlank()) {
            val credentials = settings.username + ":" + settings.password
            val token = Base64.getEncoder().encodeToString(credentials.toByteArray(Charsets.UTF_8))
            conn.setRequestProperty("Authorization", "Basic " + token)
        }
        try {
            check(conn.responseCode in 200..299) { "OpenWebif HTTP " + conn.responseCode }
            return conn.inputStream.bufferedReader().use { it.readText() }
        } finally { conn.disconnect() }
    }
    suspend fun ping(): String = withContext(Dispatchers.IO) {
        val response = JSONObject(request("/api/about"))
        check(response.has("info") || response.has("result") || response.has("enigma2")) {
            "Réponse OpenWebif non reconnue"
        }
        "Connexion Vu+ établie"
    }
    suspend fun satellites(): List<Satellite> = withContext(Dispatchers.IO) {
        val items = JSONObject(request("/api/getsatellites?stype=tv")).optJSONArray("satellites") ?: JSONArray()
        (0 until items.length()).mapNotNull { i ->
            val item = items.getJSONObject(i); val ref = item.optString("service")
            if (ref.isBlank() || ref.contains("flags == 64")) null
            else Satellite(item.optString("name").removeSuffix(" - Services"), ref)
        }.distinctBy { it.ref }
    }
    /** One native folder level; retain references, never infer identity from display names. */
    suspend fun entries(ref: String? = null): List<ServiceEntry> = withContext(Dispatchers.IO) {
        val path = "/api/getservices" + if (ref == null) "" else "?sRef=" + URLEncoder.encode(ref, "UTF-8")
        val items = JSONObject(request(path)).optJSONArray("services") ?: JSONArray()
        (0 until items.length()).mapNotNull { i ->
            val item = items.getJSONObject(i)
            val reference = item.optString("servicereference", item.optString("sref"))
            val name = item.optString("servicename", item.optString("name"))
            val flags = reference.split(':').getOrNull(1)?.toIntOrNull() ?: 0
            if (reference.isBlank() || name.isBlank() || flags and (64 or 256 or 512) != 0) null
            else ServiceEntry(name, reference, isDirectoryRef(reference))
        }.distinctBy { it.ref }
    }
    suspend fun weatherLocation(): WeatherLocation = withContext(Dispatchers.IO) {
        val data = JSONObject(request("/file?action=download&file=%2Fetc%2Fenigma2%2Fmetrix-neo%2FMetrixNEO.json"))
        val lat = data.getDouble("latitude"); val lon = data.getDouble("longitude")
        require(lat in -90.0..90.0 && lon in -180.0..180.0)
        WeatherLocation(data.getString("weather_label"), lat, lon)
    }
    suspend fun satelliteChannels(satellite: Satellite): List<Channel> = withContext(Dispatchers.IO) {
        val items = JSONObject(request("/api/getservices?sRef=" + URLEncoder.encode(satellite.ref, "UTF-8"))).optJSONArray("services") ?: JSONArray()
        (0 until items.length()).mapNotNull { i ->
            val item = items.getJSONObject(i); val ref = item.optString("servicereference")
            val flags = ref.split(':').getOrNull(1)?.toIntOrNull() ?: 0
            if (ref.isBlank() || (flags and (64 or 256 or 512)) != 0) null
            else Channel(item.optString("servicename"), ref, satellite.name)
        }.distinctBy { it.ref }
    }
    suspend fun channels(): List<Channel> = withContext(Dispatchers.IO) {
        val channels = ArrayList<Channel>()
        val seen = HashSet<String>()
        fun collect(items: JSONArray?, bouquet: String, depth: Int) {
            if (items == null || depth > 5) return
            for (i in 0 until items.length()) {
                val node = items.optJSONObject(i) ?: continue
                val name = node.optString("servicename", node.optString("name"))
                val ref = node.optString("servicereference", node.optString("sref", node.optString("reference")))
                val descendants = node.optJSONArray("subservices")
                    ?: node.optJSONArray("services") ?: node.optJSONArray("channels")
                if (descendants != null) collect(descendants, if (name.isBlank()) bouquet else name, depth + 1)
                else if (ref.isNotBlank() && name.isNotBlank() && seen.add(bouquet + "|" + ref)) {
                    val flags = ref.split(':').getOrNull(1)?.toIntOrNull() ?: 0
                    if ((flags and 64) == 0 && (flags and 256) == 0 && (flags and 512) == 0 && !isDirectoryRef(ref))
                        channels.add(Channel(name, ref, bouquet,
                            node.optString("eventtitle", node.optString("now_title")),
                            node.optString("next_title")))
                }
            }
        }
        try {
            val all = JSONObject(request("/api/getallservices"))
            collect(all.optJSONArray("services") ?: all.optJSONArray("bouquets"), "TV", 0)
        } catch (_: Exception) { /* fallback below */ }
        if (channels.isEmpty()) {
            val bouquets = JSONObject(request("/api/getservices")).optJSONArray("services") ?: JSONArray()
            for (i in 0 until bouquets.length()) {
                val bouquet = bouquets.optJSONObject(i) ?: continue
                val ref = bouquet.optString("servicereference")
                if (ref.isBlank()) continue
                try {
                    val path = "/api/getservices?sRef=" + URLEncoder.encode(ref, "UTF-8")
                    collect(JSONObject(request(path)).optJSONArray("services"), bouquet.optString("servicename", "TV"), 0)
                } catch (_: Exception) { /* skip unavailable bouquet */ }
            }
        }
        channels
    }
    suspend fun programmes(channel: Channel): List<Programme> = withContext(Dispatchers.IO) {
        val until = System.currentTimeMillis() / 1000 + 24 * 3600
        val events = JSONObject(request("/api/epgservice?sRef=" + URLEncoder.encode(channel.ref, "UTF-8") + "&endTime=" + until))
            .optJSONArray("events") ?: JSONArray()
        fun text(value: String) = Html.fromHtml(value, Html.FROM_HTML_MODE_LEGACY).toString().trim()
        (0 until events.length()).mapNotNull { index ->
            val e = events.optJSONObject(index) ?: return@mapNotNull null
            val title = text(e.optString("title"))
            if (title.isBlank()) null else Programme(title,
                listOf(text(e.optString("shortdesc")), text(e.optString("longdesc"))).filter { it.isNotBlank() }.distinct().joinToString("\n\n"),
                e.optLong("begin_timestamp"), e.optLong("duration_sec", e.optLong("duration") * 60))
        }.filter { it.begin + it.duration > System.currentTimeMillis() / 1000 }.sortedBy { it.begin }
    }
    suspend fun picon(channel: Channel): Bitmap? = withContext(Dispatchers.IO) {
        validateHost(settings.host)
        val conn = URL("http://${settings.host}:${settings.port}/api/getpicon?sRef=" + URLEncoder.encode(channel.ref, "UTF-8"))
            .openConnection() as HttpURLConnection
        conn.connectTimeout = 3000; conn.readTimeout = 3000; conn.instanceFollowRedirects = false
        if (settings.username.isNotBlank()) conn.setRequestProperty("Authorization", "Basic " +
            Base64.getEncoder().encodeToString((settings.username + ":" + settings.password).toByteArray(Charsets.UTF_8)))
        try { if (conn.responseCode == 200) conn.inputStream.use { BitmapFactory.decodeStream(it) } else null }
        finally { conn.disconnect() }
    }
    suspend fun timers(): List<String> = withContext(Dispatchers.IO) {
        val data = JSONObject(request("/api/timerlist")).optJSONArray("timers") ?: JSONArray()
        (0 until data.length()).map { i -> val t = data.getJSONObject(i)
            t.optString("name") + "  •  " + t.optString("servicename") + "  •  " +
                java.text.SimpleDateFormat("dd/MM HH:mm", java.util.Locale.FRANCE).format(java.util.Date(t.optLong("begin") * 1000)) }
    }
    suspend fun stream(channel: Channel): String = withContext(Dispatchers.IO) {
        streamUrls.get(channel.ref)?.let { return@withContext it }
        embeddedIptvAddress(channel.ref)?.let { address ->
            streamUrls.put(channel.ref, address)
            return@withContext address
        }
        val m3u = request("/web/stream.m3u?ref=" + URLEncoder.encode(channel.ref, "UTF-8"))
        val url = m3u.lineSequence().map { it.trim() }
            .firstOrNull { it.startsWith("http://") || it.startsWith("https://") }
            ?: error("Le Vu+ ne fournit pas de flux pour cette chaîne")
        checkedStreamAddress(url)
        streamUrls.put(channel.ref, url)
        url
    }
}
