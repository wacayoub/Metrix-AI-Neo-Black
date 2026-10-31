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

data class Channel(
    val name: String,
    val ref: String,
    val bouquet: String = "TV",
    val current: String = "",
    val next: String = ""
)

data class ReceiverSettings(val host: String = "192.168.11.2", val port: Int = 80,
    val username: String = "", val password: String = "")

/** OpenWebif read-only API: no zap, timer, plugin or settings changes. */
class OpenWebif(private val settings: ReceiverSettings) {
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
                else if (ref.isNotBlank() && name.isNotBlank() && seen.add(ref)) {
                    val flags = ref.split(':').getOrNull(1)?.toIntOrNull() ?: 0
                    if ((flags and 64) == 0 && (flags and 256) == 0)
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
    suspend fun stream(channel: Channel): String = withContext(Dispatchers.IO) {
        val m3u = request("/web/stream.m3u?ref=" + URLEncoder.encode(channel.ref, "UTF-8"))
        val url = m3u.lineSequence().map { it.trim() }
            .firstOrNull { it.startsWith("http://") || it.startsWith("https://") }
            ?: error("Le Vu+ ne fournit pas de flux pour cette chaîne")
        val address = InetAddress.getByName(URL(url).host)
        require(address.isSiteLocalAddress || address.isLoopbackAddress || address.isLinkLocalAddress) {
            "Streaming externe désactivé dans cette Alpha"
        }
        url
    }
}
