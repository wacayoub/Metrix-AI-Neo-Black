package com.metrixneo.tv.data

import java.net.URI

fun embeddedIptvAddress(ref: String): String? {
    if (isDirectoryRef(ref)) return null
    // Enigma2 field 10 is the URL; field 11 is a display name, never part of the URL.
    // Decode the service-reference colon escape only; preserve signed query/path escapes.
    val address = ref.split(':').getOrNull(10)?.replace("%3a", ":", ignoreCase = true) ?: return null
    if (!address.startsWith("http://", true) && !address.startsWith("https://", true)) return null
    return checkedStreamAddress(address)
}

/** Stream addresses come from the user's receiver; OpenWebif itself remains LAN-only. */
fun checkedStreamAddress(value: String): String {
    val uri = try { URI(value) } catch (_: Exception) { throw IllegalArgumentException("Adresse de flux invalide") }
    require(uri.scheme?.lowercase() in listOf("http", "https") && !uri.host.isNullOrBlank() &&
        (uri.port == -1 || uri.port in 1..65535)) { "Adresse de flux HTTP(S) invalide" }
    return value
}

fun usesReceiverAuthentication(url: String, settings: ReceiverSettings): Boolean {
    val uri = URI(checkedStreamAddress(url))
    val port = if (uri.port != -1) uri.port else if (uri.scheme.equals("https", true)) 443 else 80
    return uri.host.equals(settings.host, true) && port in setOf(settings.port, 8001, 8002)
}
