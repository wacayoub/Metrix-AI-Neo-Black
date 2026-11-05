package com.metrixneo.tv.connect

import org.json.JSONObject
import java.net.Inet6Address
import java.net.InetAddress
import java.util.Base64

internal fun privateV4(value: String): Boolean {
    val p = value.split('.')
    if (p.size != 4 || p.any { !it.matches(Regex("0|[1-9][0-9]{0,2}")) }) return false
    val n = p.map { it.toInt() }
    return n.all { it in 0..255 } && (n[0] == 10 || n[0] == 192 && n[1] == 168 || n[0] == 172 && n[1] in 16..31)
}

internal fun checkedKey(value: String): String {
    val bytes = runCatching { Base64.getDecoder().decode(value) }.getOrNull()
    require(bytes != null && bytes.size == 32 && bytes.any { it != 0.toByte() } && Base64.getEncoder().encodeToString(bytes) == value) { "Clé WireGuard invalide" }
    return value
}

internal fun checkedEndpoint(value: String): String {
    require(value.length in 3..260 && value.none { it.isWhitespace() || it in "/\\?#@" }) { "Adresse Internet invalide" }
    val match = Regex("(?:\\[([0-9a-fA-F:]+)\\]|([a-zA-Z0-9][a-zA-Z0-9.-]{0,252})):([0-9]{1,5})").matchEntire(value)
        ?: throw IllegalArgumentException("Adresse Internet invalide")
    if (match.groupValues[1].isNotEmpty()) require(InetAddress.getByName(match.groupValues[1]) is Inet6Address)
    require(match.groupValues[3].toInt() in 1..65535) { "Port Internet invalide" }
    return value
}

internal class ConnectProfile(
    val privateKey: String,
    val serverPublicKey: String,
    val address: String,
    val endpoint: String,
    val receiverHost: String,
    val receiverPort: Int,
    val certificate: String
) {
    init {
        checkedKey(privateKey); checkedKey(serverPublicKey); checkedEndpoint(endpoint)
        require(address.matches(Regex("10\\.78\\.0\\.[2-9]/32"))) { "Adresse du tunnel invalide" }
        require(privateV4(receiverHost) && !receiverHost.startsWith("10.78.0.")) { "Adresse du Vu+ invalide" }
        require(receiverPort in 1..65535 && certificate.matches(Regex("[A-F0-9]{64}"))) { "Profil invalide" }
    }

    fun wireGuardConfig(packageName: String): String {
        require(packageName.matches(Regex("[a-zA-Z0-9_.]+")))
        return """
            [Interface]
            PrivateKey = $privateKey
            Address = $address
            MTU = 1380
            IncludedApplications = $packageName

            [Peer]
            PublicKey = $serverPublicKey
            Endpoint = $endpoint
            AllowedIPs = $receiverHost/32
            PersistentKeepalive = 25
        """.trimIndent()
    }

    fun encode(): String = JSONObject().put("protocol", 1).put("privateKey", privateKey)
        .put("serverPublicKey", serverPublicKey).put("address", address).put("endpoint", endpoint)
        .put("receiverHost", receiverHost).put("receiverPort", receiverPort).put("certificate", certificate).toString()

    override fun toString() = "NeoConnectProfile(redacted)"

    fun withEndpoint(value: String) = ConnectProfile(privateKey, serverPublicKey, address, checkedEndpoint(value), receiverHost, receiverPort, certificate)

    companion object {
        fun fromPairing(privateKey: String, host: String, port: Int, certificate: String, response: JSONObject): ConnectProfile {
            require(response.getInt("protocol") == 1 && response.getString("receiver_host") == host && response.getInt("receiver_port") == port)
            require(response.getInt("mtu") == 1380)
            return ConnectProfile(privateKey, response.getString("server_public_key"), response.getString("address"),
                response.getString("endpoint"), host, port, certificate)
        }

        fun decode(value: String): ConnectProfile {
            val j = JSONObject(value)
            require(j.getInt("protocol") == 1)
            return ConnectProfile(j.getString("privateKey"), j.getString("serverPublicKey"), j.getString("address"),
                j.getString("endpoint"), j.getString("receiverHost"), j.getInt("receiverPort"), j.getString("certificate"))
        }
    }
}
