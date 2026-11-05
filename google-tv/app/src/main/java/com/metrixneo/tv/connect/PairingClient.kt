package com.metrixneo.tv.connect

import com.wireguard.crypto.KeyPair
import org.json.JSONObject
import java.net.InetSocketAddress
import java.net.URL
import java.io.ByteArrayOutputStream
import java.security.MessageDigest
import java.security.SecureRandom
import java.security.cert.CertificateException
import java.security.cert.X509Certificate
import javax.net.ssl.HttpsURLConnection
import javax.net.ssl.SSLContext
import javax.net.ssl.SSLSocket
import javax.net.ssl.TrustManager
import javax.net.ssl.X509TrustManager

internal class PairingClient {
    private fun context(pin: String?): SSLContext = SSLContext.getInstance("TLS").apply {
        init(null, arrayOf<TrustManager>(object : X509TrustManager {
            override fun getAcceptedIssuers(): Array<X509Certificate> = emptyArray()
            override fun checkClientTrusted(chain: Array<X509Certificate>, type: String) { throw CertificateException() }
            override fun checkServerTrusted(chain: Array<X509Certificate>, type: String) {
                if (chain.isEmpty() || chain.size > 5) throw CertificateException()
                chain[0].checkValidity()
                // Discovery sends no secret or HTTP request. Pairing requires the exact
                // certificate fingerprint physically confirmed on the receiver screen.
                if (pin != null && !MessageDigest.isEqual(fingerprint(chain[0]).toByteArray(), pin.toByteArray())) throw CertificateException()
            }
        }), SecureRandom())
    }

    fun discover(host: String): String {
        require(privateV4(host)) { "Utiliser l’adresse IPv4 privée du Vu+" }
        return (context(null).socketFactory.createSocket() as SSLSocket).use { socket ->
            socket.soTimeout = 5000
            socket.connect(InetSocketAddress(host, 9843), 5000)
            socket.startHandshake()
            fingerprint(socket.session.peerCertificates[0] as X509Certificate)
        }
    }

    fun pair(host: String, receiverPort: Int, fingerprint: String, code: String, name: String): ConnectProfile {
        require(privateV4(host) && fingerprint.matches(Regex("[A-F0-9]{64}")) && code.matches(Regex("[0-9]{6}")))
        require(name.matches(Regex("[\\p{L}\\p{N}_ .-]{1,40}")))
        val keys = KeyPair()
        val bytes = JSONObject().put("code", code).put("public_key", keys.publicKey.toBase64()).put("name", name).toString().toByteArray(Charsets.UTF_8)
        val connection = URL("https://$host:9843/pair").openConnection() as HttpsURLConnection
        connection.sslSocketFactory = context(fingerprint).socketFactory
        connection.hostnameVerifier = javax.net.ssl.HostnameVerifier { requested, _ -> requested == host }
        connection.instanceFollowRedirects = false
        connection.connectTimeout = 5000; connection.readTimeout = 8000
        connection.requestMethod = "POST"; connection.doOutput = true
        connection.setRequestProperty("Content-Type", "application/json")
        connection.setFixedLengthStreamingMode(bytes.size)
        try {
            connection.outputStream.use { it.write(bytes) }
            check(connection.responseCode == 200) { "Association refusée. Renouveler le code sur le Vu+." }
            val response = connection.inputStream.use { input ->
                val out = ByteArrayOutputStream()
                val buffer = ByteArray(1024)
                while (out.size() <= 4096) {
                    val count = input.read(buffer, 0, minOf(buffer.size, 4097 - out.size()))
                    if (count < 0) break
                    out.write(buffer, 0, count)
                }
                val data = out.toByteArray()
                require(data.size <= 4096)
                JSONObject(String(data, Charsets.UTF_8))
            }
            return ConnectProfile.fromPairing(keys.privateKey.toBase64(), host, receiverPort, fingerprint, response)
        } finally { connection.disconnect() }
    }

    private fun fingerprint(certificate: X509Certificate): String = MessageDigest.getInstance("SHA-256").digest(certificate.encoded)
        .joinToString("") { "%02X".format(it.toInt() and 255) }
}
