package com.metrixneo.tv.data

/** Session-only URLs: bounded, expiring and never shared between receiver credentials. */
internal class StreamUrlCache(
    private val capacity: Int = 64,
    private val ttlMs: Long = 300_000,
    private val now: () -> Long = { System.nanoTime() / 1_000_000 }
) {
    private data class Entry(val url: String, val expires: Long)
    private val entries = LinkedHashMap<String, Entry>(capacity, .75f, true)
    init { require(capacity > 0 && ttlMs > 0) }
    @Synchronized fun get(ref: String): String? {
        val entry = entries[ref] ?: return null
        if (entry.expires <= now()) { entries.remove(ref); return null }
        return entry.url
    }
    @Synchronized fun put(ref: String, url: String) {
        entries[ref] = Entry(url, now() + ttlMs)
        while (entries.size > capacity) entries.remove(entries.keys.first())
    }
    @Synchronized fun remove(ref: String) { entries.remove(ref) }
}
