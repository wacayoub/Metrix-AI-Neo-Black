package com.metrixneo.tv

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import com.metrixneo.tv.data.ReceiverSettings
import com.metrixneo.tv.data.ResumeState
import java.security.KeyStore
import java.util.concurrent.atomic.AtomicLong
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

/** Service references may contain IPTV tokens. Persist only an encrypted, receiver-bound bookmark. */
internal class ResumeStore(context: Context) {
    private val prefs = context.getSharedPreferences("resume-v1", Context.MODE_PRIVATE)
    private val generation = AtomicLong()
    private var cachedKey: SecretKey? = null
    private fun aad(config: ReceiverSettings) = "${config.host}:${config.port}:${config.username}".toByteArray(Charsets.UTF_8)
    private fun key(create: Boolean): SecretKey? {
        cachedKey?.let { return it }
        val store = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        (store.getKey("metrixneo.resume", null) as? SecretKey)?.let { cachedKey = it; return it }
        if (!create) return null
        return KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore").apply {
            init(KeyGenParameterSpec.Builder("metrixneo.resume", KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).build())
        }.generateKey().also { cachedKey = it }
    }
    fun nextGeneration(): Long = generation.incrementAndGet()
    @Synchronized fun read(config: ReceiverSettings): ResumeState? = try {
        val blob = prefs.getString("bookmark", null)
        val iv = prefs.getString("iv", null)
        val secret = key(false)
        if (blob == null || iv == null || secret == null || blob.length > 200000) null else {
            val cipher = Cipher.getInstance("AES/GCM/NoPadding")
            cipher.init(Cipher.DECRYPT_MODE, secret, GCMParameterSpec(128, Base64.decode(iv, Base64.NO_WRAP)))
            cipher.updateAAD(aad(config))
            ResumeState.decode(String(cipher.doFinal(Base64.decode(blob, Base64.NO_WRAP)), Charsets.UTF_8))
        }
    } catch (_: Exception) { null }
    @Synchronized fun write(config: ReceiverSettings, state: ResumeState, request: Long) {
        if (request != generation.get()) return
        try {
            val text = state.encode(); if (text.length > 131072) return
            val cipher = Cipher.getInstance("AES/GCM/NoPadding")
            cipher.init(Cipher.ENCRYPT_MODE, requireNotNull(key(true))); cipher.updateAAD(aad(config))
            val blob = cipher.doFinal(text.toByteArray(Charsets.UTF_8))
            if (request != generation.get()) return
            prefs.edit().putString("bookmark", Base64.encodeToString(blob, Base64.NO_WRAP))
                .putString("iv", Base64.encodeToString(cipher.iv, Base64.NO_WRAP)).apply()
        } catch (_: Exception) { /* A device key/storage failure must not block navigation or playback. */ }
    }
}
