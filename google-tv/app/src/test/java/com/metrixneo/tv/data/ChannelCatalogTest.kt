package com.metrixneo.tv.data

import org.junit.Assert.*
import org.junit.Test

class ChannelCatalogTest {
    @Test fun sameServiceRemainsInItsBouquetsButAppearsOnceInAllServices() {
        val first = Channel("One", "ref1", "B")
        val second = Channel("Two", "ref2", "A")
        val duplicate = Channel("One again", "ref1", "A")
        val catalog = ChannelCatalog(listOf(first, second, duplicate))
        assertEquals(listOf("B", "A"), catalog.names)
        assertEquals(listOf(first, second), catalog.all)
        assertEquals(listOf(second, duplicate), catalog.bouquet("A"))
        assertEquals(2, catalog.count("A"))
        assertTrue(catalog.bouquet("missing").isEmpty())
    }

    @Test fun pagingLargeListDoesNotVisitDiscardedChannels() {
        var reads = 0
        val source = object : AbstractList<Int>() {
            override val size = 100_000
            override fun get(index: Int): Int { reads++; return index }
        }
        val page = pageWindow(source, 50_000)
        assertEquals(0, reads)
        assertEquals((50_000..50_019).toList(), page.toList())
        assertEquals(20, reads)
    }

    @Test fun finalPageAndEmptyListStayWithinBounds() {
        assertEquals(listOf(40, 41), pageWindow((0..41).toList(), 40))
        assertTrue(pageWindow(emptyList<Int>(), 20).isEmpty())
        assertTrue(pageWindow(listOf(1), Int.MAX_VALUE).isEmpty())
        assertEquals(listOf(1), pageWindow(listOf(1), -20))
    }
}
