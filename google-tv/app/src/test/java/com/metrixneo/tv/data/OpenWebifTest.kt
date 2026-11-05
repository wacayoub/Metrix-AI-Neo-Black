package com.metrixneo.tv.data

import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Test
import java.net.InetAddress
import java.net.ServerSocket
import kotlin.concurrent.thread

/** Local HTTP fixtures exercise the real GET/parser path without contacting a receiver. */
class OpenWebifTest {
    private fun withServer(routes: Map<String, String>, test: (OpenWebif, MutableList<String>) -> Unit) {
        val calls = java.util.Collections.synchronizedList(mutableListOf<String>())
        val server = ServerSocket(0, 50, InetAddress.getByName("127.0.0.1"))
        val worker = thread(isDaemon = true) {
            while (!server.isClosed) {
                val socket = try { server.accept() } catch (_: java.net.SocketException) { break }
                socket.use {
                    it.soTimeout = 5000
                    val reader = it.getInputStream().bufferedReader()
                    val parts = reader.readLine().split(' ')
                    calls.add(parts[0] + " " + parts[1])
                    while (!reader.readLine().isNullOrBlank()) { /* consume request headers */ }
                    val body = routes[parts[1]]
                    val bytes = (body ?: "unavailable").toByteArray()
                    val out = it.getOutputStream()
                    out.write(("HTTP/1.1 " + (if (body == null) "404 Not Found" else "200 OK") +
                        "\r\nContent-Length: ${bytes.size}\r\nConnection: close\r\n\r\n").toByteArray())
                    out.write(bytes); out.flush()
                }
            }
        }
        try { test(OpenWebif(ReceiverSettings("127.0.0.1", server.localPort)), calls) }
        finally { server.close(); worker.join(1000) }
    }

    @Test fun sameServiceRemainsInEachBouquetAndMarkersAreNotPlayable() {
        withServer(mapOf("/api/getallservices" to """{"services":[
          {"servicename":"Favoris","subservices":[
            {"servicename":"One","servicereference":"1:0:1:A:0:0:0:0:0:0:"},
            {"servicename":"Marker","servicereference":"1:64:1:0:"},
            {"servicename":"Hidden","servicereference":"1:512:1:0:"}]},
          {"servicename":"Autre","subservices":[
            {"servicename":"One","servicereference":"1:0:1:A:0:0:0:0:0:0:"}]}]}""")) { api, calls ->
            val channels = runBlocking { api.channels() }
            assertEquals(listOf("Favoris", "Autre"), channels.map { it.bouquet })
            assertEquals(1, channels.map { it.ref }.distinct().size)
            assertTrue(calls.all { it.startsWith("GET ") })
        }
    }

    @Test fun unavailableBulkEndpointFallsBackToBouquetServices() {
        withServer(mapOf(
            "/api/getservices" to """{"services":[{"servicename":"Local","servicereference":"b1"}]}""",
            "/api/getservices?sRef=b1" to """{"services":[{"servicename":"News","servicereference":"1:0:1:B:0:"}]}"""
        )) { api, calls ->
            val channels = runBlocking { api.channels() }
            assertEquals("News", channels.single().name)
            assertEquals("Local", channels.single().bouquet)
            assertEquals(3, calls.size)
            assertTrue(calls.all { it.startsWith("GET ") })
        }
    }

    @Test fun publicStreamFromTheReceiverIsResolvedWithoutOpeningIt() {
        withServer(mapOf("/web/stream.m3u?ref=x" to "#EXTM3U\nhttp://8.8.8.8:8001/live\n")) { api, calls ->
            assertEquals("http://8.8.8.8:8001/live", runBlocking { api.stream(Channel("Test", "x")) })
            assertEquals(listOf("GET /web/stream.m3u?ref=x"), calls)
        }
    }
    @Test fun receiverCredentialsAreNotSelectedForInternetProvidersOrLookalikeHosts() {
        val settings = ReceiverSettings("192.168.11.2", 82, "test", "example")
        assertTrue(usesReceiverAuthentication("http://192.168.11.2:8001/live", settings))
        assertTrue(usesReceiverAuthentication("http://192.168.11.2:82/stream", settings))
        assertFalse(usesReceiverAuthentication("https://provider.example/live", settings))
        assertFalse(usesReceiverAuthentication("http://192.168.11.2.example/live", settings))
        assertFalse(usesReceiverAuthentication("http://192.168.11.2:9999/live", settings))
        assertFalse(usesReceiverAuthentication("http://192.168.11.2@provider.example/live", settings))
    }
    @Test fun nonHttpStreamSchemesAreRejected() {
        assertTrue(runCatching { checkedStreamAddress("file:///etc/passwd") }.isFailure)
        assertTrue(runCatching { checkedStreamAddress("http://") }.isFailure)
    }
    @Test fun embeddedIptvUrlExcludesTheChannelLabelAndPreservesSignedEscapes() {
        val ref = "4097:0:1:0:0:0:0:0:0:0:https%3a//provider.example%3a8443/live/a/b/42.ts?token=a%2Bb%2Fc:|FR| TF1 FHD"
        assertEquals("https://provider.example:8443/live/a/b/42.ts?token=a%2Bb%2Fc", embeddedIptvAddress(ref))
        withServer(emptyMap()) { api, calls ->
            assertEquals(embeddedIptvAddress(ref), runBlocking { api.stream(Channel("TF1", ref)) })
            assertTrue(calls.isEmpty())
        }
        assertNull(embeddedIptvAddress("1:0:19:1:2:3:4:0:0:0:"))
    }

    @Test fun returningToAChannelReusesOnlyItsValidatedUrl() {
        withServer(mapOf("/web/stream.m3u?ref=x" to "#EXTM3U\nhttp://127.0.0.1:8001/x\n")) { api, calls ->
            val ch = Channel("Test", "x")
            assertNull(api.cachedStream(ch))
            val first = runBlocking { api.stream(ch) }
            assertEquals(first, runBlocking { api.stream(ch) })
            assertEquals(first, api.cachedStream(ch))
            assertEquals(listOf("GET /web/stream.m3u?ref=x"), calls)
        }
    }

    @Test fun cachedUrlsExpireRatherThanKeepingStaleStreamTokens() {
        var clock = 0L
        val cache = StreamUrlCache(ttlMs = 100, now = { clock })
        cache.put("one", "url")
        clock = 99
        assertEquals("url", cache.get("one"))
        clock = 100
        assertNull(cache.get("one"))
    }
    @Test fun satellitesUseReceiverReferencesAndExcludeNewServiceFolders() {
        withServer(mapOf(
            "/api/getsatellites?stype=tv" to """{"satellites":[{"name":"13.0E Hot Bird - Services","service":"sat"},{"name":"13.0E Hot Bird - New","service":"(flags == 64)"}]}""",
            "/api/getservices?sRef=sat" to """{"services":[{"servicename":"One","servicereference":"1:0:1:A:0:"},{"servicename":"Marker","servicereference":"1:64:1:0:"}]}"""
        )) { api, calls ->
            val satellites = runBlocking { api.satellites() }
            assertEquals("13.0E Hot Bird", satellites.single().name)
            val channels = runBlocking { api.satelliteChannels(satellites.single()) }
            assertEquals("One", channels.single().name)
            assertEquals("13.0E Hot Bird", channels.single().bouquet)
            assertTrue(calls.all { it.startsWith("GET ") })
        }
    }

    @Test fun cacheIsBoundedAndRetainsTheMostRecentlyUsedChannel() {
        val cache = StreamUrlCache(capacity = 2)
        cache.put("one", "1"); cache.put("two", "2")
        assertEquals("1", cache.get("one"))
        cache.put("three", "3")
        assertNull(cache.get("two"))
        assertEquals("1", cache.get("one"))
        assertEquals("3", cache.get("three"))
    }
    @Test fun nativeFoldersCanBeOpenedAtMultipleLevelsWithoutPlayingDirectoryReferences() {
        withServer(mapOf(
            "/api/getservices" to """{"services":[{"servicename":"IPTV","servicereference":"1:7:root"}]}""",
            "/api/getservices?sRef=1%3A7%3Aroot" to """{"services":[{"servicename":"France","servicereference":"1:7:fr"},{"servicename":"Same name","servicereference":"1:7:other"},{"servicename":"Marker","servicereference":"1:64:0"}]}""",
            "/api/getservices?sRef=1%3A7%3Afr" to """{"services":[{"servicename":"News","servicereference":"4097:0:1"},{"servicename":"News","servicereference":"4097:0:2"}]}"""
        )) { api, calls ->
            val root = runBlocking { api.entries() }.single()
            assertTrue(root.directory)
            val subfolders = runBlocking { api.entries(root.ref) }
            assertEquals(2, subfolders.size)
            assertTrue(subfolders.all { it.directory })
            val channels = runBlocking { api.entries(subfolders.first().ref) }
            assertEquals(2, channels.size)
            assertTrue(channels.none { it.directory })
            assertNotEquals(channels[0].ref, channels[1].ref)
            assertEquals(3, calls.size)
            assertTrue(calls.all { it.startsWith("GET /api/getservices") })
        }
    }
    @Test fun groupReferencesAreFoldersButPlayableServiceTypesAreNot() {
        assertTrue(isDirectoryRef("1:7:folder"))
        assertTrue(isDirectoryRef("1:134:alternative"))
        assertFalse(isDirectoryRef("1:0:19:channel"))
        assertFalse(isDirectoryRef("4097:0:1:iptv"))
    }
}
