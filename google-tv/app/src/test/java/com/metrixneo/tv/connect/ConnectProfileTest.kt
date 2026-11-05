package com.metrixneo.tv.connect

import org.junit.Assert.*
import org.junit.Test
import java.util.Base64
import org.json.JSONObject
import com.wireguard.config.Config

class ConnectProfileTest {
    private fun key(n: Int) = Base64.getEncoder().encodeToString(ByteArray(32) { n.toByte() })
    private fun profile() = ConnectProfile(key(1), key(2), "10.78.0.2/32", "home.example:51820", "192.168.11.2", 82, "AB".repeat(32))

    @Test fun literalPrivateAddressesOnly() {
        for (ip in listOf("192.168.11.2", "10.0.0.2", "172.31.2.3")) assertTrue(privateV4(ip))
        for (ip in listOf("8.8.8.8", "127.0.0.1", "100.64.1.1", "192.168.11.2.example", "192.168.011.2", "192.168.1.999", "::1")) assertFalse(privateV4(ip))
    }

    @Test fun endpointRejectsUrlsCredentialsAndInjection() {
        for (v in listOf("home.example:51820", "1.2.3.4:12", "[2001:db8::1]:51820")) assertEquals(v, checkedEndpoint(v))
        for (v in listOf("https://home:443", "home:0", "user:pass@host:1234", "host:51820\nAllowedIPs = 0.0.0.0/0", "home:65536", "host:1234/path")) assertTrue(runCatching { checkedEndpoint(v) }.isFailure)
    }

    @Test fun configRoutesOnlyReceiverAndOnlyNeo() {
        val text = profile().wireGuardConfig("com.metrixneo.tv")
        assertTrue(text.contains("AllowedIPs = 192.168.11.2/32"))
        assertTrue(text.contains("IncludedApplications = com.metrixneo.tv"))
        assertFalse(text.contains("0.0.0.0/0"))
        assertFalse(text.contains("DNS ="))
        assertTrue(runCatching { profile().wireGuardConfig("pkg\nDNS = 1.1.1.1") }.isFailure)
    }

    @Test fun secretProfileRoundTripAndRedactedToString() {
        val value = profile()
        val restored = ConnectProfile.decode(value.encode())
        assertEquals(value.wireGuardConfig("com.metrixneo.tv"), restored.wireGuardConfig("com.metrixneo.tv"))
        assertFalse(value.toString().contains(key(1)))
    }

    @Test fun invalidProfileKeysAndAddressesRejected() {
        for (address in listOf("0.0.0.0/0", "10.78.0.1/32", "10.78.0.2/24", "10.78.0.10/32")) {
            assertTrue(runCatching { ConnectProfile(key(1), key(2), address, "host:51820", "192.168.1.2", 82, "AB".repeat(32)) }.isFailure)
        }
        assertTrue(runCatching { checkedKey(Base64.getEncoder().encodeToString(ByteArray(32))) }.isFailure)
        assertTrue(runCatching { checkedKey("invalid") }.isFailure)
    }

    @Test fun officialParserAcceptsRestrictedConfiguration() {
        val parsed = Config.parse(profile().wireGuardConfig("com.metrixneo.tv").byteInputStream())
        assertEquals(setOf("com.metrixneo.tv"), parsed.`interface`.includedApplications)
        assertEquals(1, parsed.peers.size)
        assertEquals(setOf("192.168.11.2/32"), parsed.peers[0].allowedIps.map { it.toString() }.toSet())
    }

    @Test fun pairedResponseCannotSwitchReceiverOrWidenRoutes() {
        fun reply() = JSONObject().put("protocol", 1).put("receiver_host", "192.168.11.2").put("receiver_port", 82)
            .put("mtu", 1380).put("server_public_key", key(2)).put("address", "10.78.0.2/32").put("endpoint", "home.example:51820")
        fun read(j: JSONObject) = ConnectProfile.fromPairing(key(1), "192.168.11.2", 82, "AB".repeat(32), j)
        assertEquals("192.168.11.2", read(reply()).receiverHost)
        for (j in listOf(reply().put("receiver_host", "192.168.11.3"), reply().put("receiver_port", 443), reply().put("mtu", 9000),
            reply().put("address", "0.0.0.0/0"), reply().put("protocol", 2))) assertTrue(runCatching { read(j) }.isFailure)
    }
}
