package com.metrixneo.tv.connect

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

internal class ConnectStore(context: Context) {
    private val prefs = context.getSharedPreferences("neo_connect", Context.MODE_PRIVATE)
    private val alias = "metrixneo.connect.profile"
    private val aad = "NeoConnect:1:${context.packageName}".toByteArray()

    private fun key(create: Boolean): SecretKey? {
        val store = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        (store.getKey(alias, null) as? SecretKey)?.let { return it }
        if (!create) return null
        return KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore").apply {
            init(KeyGenParameterSpec.Builder(alias, KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).build())
        }.generateKey()
    }

    fun save(profile: ConnectProfile) {
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, requireNotNull(key(true)))
        cipher.updateAAD(aad)
        val bytes = cipher.doFinal(profile.encode().toByteArray(Charsets.UTF_8))
        check(prefs.edit().putString("data", Base64.encodeToString(bytes, Base64.NO_WRAP))
            .putString("iv", Base64.encodeToString(cipher.iv, Base64.NO_WRAP)).commit())
    }

    fun load(): ConnectProfile? {
        val data = prefs.getString("data", null) ?: return null
        val iv = prefs.getString("iv", null) ?: return null
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.DECRYPT_MODE, key(false) ?: error("Clé Android indisponible"), GCMParameterSpec(128, Base64.decode(iv, Base64.NO_WRAP)))
        cipher.updateAAD(aad)
        return ConnectProfile.decode(String(cipher.doFinal(Base64.decode(data, Base64.NO_WRAP)), Charsets.UTF_8))
    }

    fun exists() = prefs.contains("data")
    fun clear() { check(prefs.edit().clear().commit()) }
}
