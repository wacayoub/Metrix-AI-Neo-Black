package com.metrixneo.tv

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import com.metrixneo.tv.data.ReceiverSettings
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

/** TV process recreation must not require typing the receiver login again. */
internal class ReceiverCredentials(context: Context) {
    private val prefs = context.getSharedPreferences("receiver", Context.MODE_PRIVATE)
    private val alias = "metrixneo.openwebif"
    private fun key(create: Boolean): SecretKey? {
        val store = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        (store.getKey(alias, null) as? SecretKey)?.let { return it }
        if (!create) return null
        return KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore").apply {
            init(KeyGenParameterSpec.Builder(alias, KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).build())
        }.generateKey()
    }
    private fun aad(config: ReceiverSettings) = "${config.host}:${config.port}:${config.username}".toByteArray(Charsets.UTF_8)
    fun load(): ReceiverSettings {
        val config = ReceiverSettings(prefs.getString("host", "192.168.11.2")!!, prefs.getInt("port", 82), prefs.getString("username", "")!!)
        val password = try {
            val encrypted = prefs.getString("password_encrypted", null)
            val iv = prefs.getString("password_iv", null)
            val key = key(false)
            if (encrypted == null || iv == null || key == null) "" else {
                val cipher = Cipher.getInstance("AES/GCM/NoPadding")
                cipher.init(Cipher.DECRYPT_MODE, key, GCMParameterSpec(128, Base64.decode(iv, Base64.NO_WRAP)))
                cipher.updateAAD(aad(config))
                String(cipher.doFinal(Base64.decode(encrypted, Base64.NO_WRAP)), Charsets.UTF_8)
            }
        } catch (_: Exception) { "" } // Lost/revoked device key requires a fresh login.
        return config.copy(password = password)
    }
    fun save(config: ReceiverSettings) {
        val edit = prefs.edit().putString("host", config.host).putInt("port", config.port).putString("username", config.username)
        if (config.password.isEmpty()) edit.remove("password_encrypted").remove("password_iv")
        else {
            val cipher = Cipher.getInstance("AES/GCM/NoPadding")
            cipher.init(Cipher.ENCRYPT_MODE, requireNotNull(key(true)))
            cipher.updateAAD(aad(config))
            val bytes = cipher.doFinal(config.password.toByteArray(Charsets.UTF_8))
            edit.putString("password_encrypted", Base64.encodeToString(bytes, Base64.NO_WRAP))
                .putString("password_iv", Base64.encodeToString(cipher.iv, Base64.NO_WRAP))
        }
        edit.apply()
    }
}
