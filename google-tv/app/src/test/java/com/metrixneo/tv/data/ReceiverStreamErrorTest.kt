package com.metrixneo.tv.data

import org.junit.Assert.*
import org.junit.Test

class ReceiverStreamErrorTest {
    @Test fun detectsEnigmaErrorWrappedInVideoResponse() {
        val body = "HTTP/1.0 400 Bad Request\r\n\r\n".toByteArray()
        assertEquals(28, body.size)
        assertEquals(400, receiverStreamHttpError(body))
        assertEquals(409, receiverStreamHttpError("HTTP/1.1 409 Conflict\r\n".toByteArray()))
        assertEquals(503, receiverStreamHttpError("HTTP/1.0 503 Service Unavailable\r\n".toByteArray()))
    }
    @Test fun waitsForCompleteStatusWithoutConsumingExtraNetworkData() {
        val body = "HTTP/1.0 400 Bad Request".toByteArray()
        assertNull(receiverStreamHttpError(body, 9))
        assertNull(receiverStreamHttpError(body, 11))
        assertEquals(400, receiverStreamHttpError(body, 12))
    }
    @Test fun leavesTransportStreamAndOtherFormatsUntouched() {
        val ts = ByteArray(564).apply { this[0] = 0x47; this[188] = 0x47; this[376] = 0x47 }
        assertNull(receiverStreamHttpError(ts))
        assertNull(receiverStreamHttpError("#EXTM3U\n#EXTINF:2,".toByteArray()))
        assertNull(receiverStreamHttpError("HTTP/1.0 200 OK\r\n".toByteArray()))
        assertNull(receiverStreamHttpError(byteArrayOf()))
    }
    @Test fun manualRetryCanInvalidateOnlyItsOwnCachedAddress() {
        val cache = StreamUrlCache()
        cache.put("one", "http://receiver/old")
        cache.put("two", "http://receiver/two")
        cache.remove("one")
        assertNull(cache.get("one"))
        assertEquals("http://receiver/two", cache.get("two"))
    }
}
