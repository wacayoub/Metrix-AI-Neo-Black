package com.metrixneo.tv.data

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.util.LruCache
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import java.security.MessageDigest

/** Private disk cache survives process recreation; decoding and downloads never block the UI. */
class PiconStore(context: Context) {
    private val directory = File(context.cacheDir, "picons-v1").apply { mkdirs() }
    private val memory = object : LruCache<String, Bitmap>(8192) {
        override fun sizeOf(key: String, value: Bitmap) = (value.byteCount / 1024).coerceAtLeast(1)
    }
    suspend fun get(config: ReceiverSettings, channel: Channel, fetch: suspend () -> Bitmap?): Bitmap? = withContext(Dispatchers.IO) {
        val raw = "${config.host}:${config.port}:${config.username}|${channel.ref}"
        val key = MessageDigest.getInstance("SHA-256").digest(raw.toByteArray()).joinToString("") { "%02x".format(it) }
        memory.get(key)?.let { return@withContext it }
        val file = File(directory, "$key.png")
        val age = System.currentTimeMillis() - file.lastModified()
        if (file.exists() && file.length() == 0L && age < 3600000) return@withContext null
        if (file.exists() && file.length() > 0 && age < 7 * 86400000L) {
            BitmapFactory.decodeFile(file.path)?.let { memory.put(key, it); return@withContext it }
        }
        val bitmap = fetch()
        try {
            val temp = File(directory, "$key.tmp")
            temp.outputStream().use { out -> bitmap?.compress(Bitmap.CompressFormat.PNG, 100, out) }
            if (!temp.renameTo(file)) temp.delete()
            val files = directory.listFiles().orEmpty().filter { it.extension == "png" }
            if (files.size > 512 || files.sumOf { it.length() } > 32L * 1024 * 1024) {
                var size = files.sumOf { it.length() }; var count = files.size
                for (old in files.sortedBy { it.lastModified() }) {
                    if (count <= 480 && size <= 28L * 1024 * 1024) break
                    val bytes = old.length(); if (old.delete()) { size -= bytes; count-- }
                }
            }
        } catch (_: java.io.IOException) { /* Rendering remains available without disk space. */ }
        bitmap?.let { memory.put(key, it) }
        bitmap
    }
}
