package com.metrixneo.tv.data

/** Build once when the receiver list changes, never while moving the selection. */
internal class ChannelCatalog(channels: List<Channel>) {
    val groups: Map<String, List<Channel>> = channels.groupBy { it.bouquet }
    val names: List<String> = groups.keys.toList()
    val all: List<Channel> = channels.distinctBy { it.ref }
    fun bouquet(name: String): List<Channel> = groups[name].orEmpty()
    fun count(name: String): Int = groups[name]?.size ?: 0
}

/** A view of the requested rows: does not copy/traverse the discarded list tail. */
internal fun <T> pageWindow(items: List<T>, start: Int, count: Int = 20): List<T> {
    require(count > 0)
    val first = start.coerceIn(0, items.size)
    return items.subList(first, first + minOf(count, items.size - first))
}
