package com.metrixneo.tv.data

import androidx.media3.datasource.DataSource
import androidx.media3.datasource.DataSpec
import java.io.IOException

/** Enigma2 can send HTTP 200 video/mpeg followed by an HTTP error as its body. */
internal fun receiverStreamHttpError(bytes: ByteArray, length: Int = bytes.size): Int? {
    if (length < 12 || length > bytes.size) return null
    val prefix = String(bytes, 0, minOf(length, 16), Charsets.US_ASCII)
    if (!prefix.startsWith("HTTP/1.0 ") && !prefix.startsWith("HTTP/1.1 ")) return null
    return prefix.substring(9, 12).toIntOrNull()?.takeIf { it in 400..599 }
}

class ReceiverStreamException(val statusCode: Int) : IOException("Receiver streaming HTTP $statusCode")

/** Inspect the existing connection's prefix only. No extra stream, URI or payload logging. */
@androidx.annotation.OptIn(androidx.media3.common.util.UnstableApi::class)
class ReceiverStreamDataSource(private val upstream: DataSource, private val receiver: ReceiverSettings) : DataSource by upstream {
    private val prefix = ByteArray(16)
    private var used = 0
    private var inspect = false

    override fun open(dataSpec: DataSpec): Long {
        used = 0
        inspect = usesReceiverAuthentication(dataSpec.uri.toString(), receiver)
        return upstream.open(dataSpec)
    }

    override fun read(buffer: ByteArray, offset: Int, length: Int): Int {
        val count = upstream.read(buffer, offset, length)
        if (inspect && count > 0) {
            val copy = minOf(count, prefix.size - used)
            buffer.copyInto(prefix, used, offset, offset + copy)
            used += copy
            receiverStreamHttpError(prefix, used)?.let { throw ReceiverStreamException(it) }
            if (used == prefix.size || (used >= 5 && !String(prefix, 0, 5, Charsets.US_ASCII).equals("HTTP/"))) inspect = false
        }
        return count
    }
}
