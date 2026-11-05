package com.metrixneo.tv.data

import android.content.Context
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.security.MessageDigest

class ChannelStore(context: Context) {
    private val directory = File(context.cacheDir, "channels-v1").apply { mkdirs() }
    private fun file(config: ReceiverSettings): File {
        val key = MessageDigest.getInstance("SHA-256").digest("${config.host}:${config.port}:${config.username}".toByteArray()).joinToString("") { "%02x".format(it) }
        return File(directory, "$key.json")
    }
    suspend fun read(config: ReceiverSettings): List<Channel> = withContext(Dispatchers.IO) {
        val file = file(config)
        try {
            if (!file.exists() || file.length() > 16 * 1024 * 1024 || System.currentTimeMillis() - file.lastModified() > 86400000) emptyList()
            else {
                val data = JSONArray(file.readText())
                (0 until data.length()).map { i -> val c = data.getJSONObject(i); Channel(c.getString("name"), c.getString("ref"), c.getString("bouquet")) }
            }
        } catch (_: Exception) { emptyList() }
    }
    suspend fun write(config: ReceiverSettings, channels: List<Channel>) = withContext(Dispatchers.IO) {
        try {
            val data = JSONArray(); channels.forEach { data.put(JSONObject().put("name", it.name).put("ref", it.ref).put("bouquet", it.bouquet)) }
            val target = file(config); val temp = File(directory, target.name + ".tmp")
            temp.writeText(data.toString()); if (!temp.renameTo(target)) temp.delete()
            directory.listFiles().orEmpty().filter { it.name != target.name }.forEach { it.delete() }
        } catch (_: java.io.IOException) { /* Cache failure must not prevent live lists. */ }
    }
}
