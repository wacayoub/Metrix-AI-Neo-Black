package com.metrixneo.tv.connect

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.IBinder
import com.metrixneo.tv.ReceiverCredentials
import com.metrixneo.tv.data.OpenWebif
import com.wireguard.android.backend.GoBackend
import com.wireguard.android.backend.Tunnel
import com.wireguard.config.Config
import com.wireguard.crypto.Key
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow

internal data class ConnectStatus(val phase: String = "off", val message: String = "Tunnel arrêté", val rx: Long = 0, val tx: Long = 0)

internal object NeoConnect {
    var returnBackAt = -1L
    internal val mutable = MutableStateFlow(ConnectStatus())
    val status = mutable.asStateFlow()
    fun start(context: Context) = context.startForegroundService(Intent(context, NeoConnectService::class.java).setAction("up"))
    fun stop(context: Context) = context.startService(Intent(context, NeoConnectService::class.java).setAction("down"))
}

class NeoConnectService : Service() {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val guard = Any()
    @Volatile private var destroyed = false
    private var backend: GoBackend? = null
    private var running: Job? = null
    private val tunnel = object : Tunnel {
        override fun getName() = "neoconnect"
        override fun onStateChange(state: Tunnel.State) { /* Actual state is read in the monitor. */ }
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val manager = getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(NotificationChannel("neo_connect", "Neo Connect", NotificationManager.IMPORTANCE_LOW))
        val pending = PendingIntent.getActivity(this, 0, Intent(this, NeoConnectActivity::class.java), PendingIntent.FLAG_IMMUTABLE)
        startForeground(901, Notification.Builder(this, "neo_connect").setSmallIcon(android.R.drawable.stat_sys_warning)
            .setContentTitle("Neo Connect").setContentText("Connexion privée gérée par Neo — ouvrir pour vérifier ou arrêter")
            .setContentIntent(pending).setOngoing(true).build())
        if (intent?.action != "up") {
            running?.cancel()
            scope.launch { disconnect(); stopSelf(startId) }
            return START_NOT_STICKY
        }
        if (running?.isActive == true) return START_NOT_STICKY
        running = scope.launch {
            try {
                NeoConnect.mutable.value = ConnectStatus("starting", "Préparation du tunnel…")
                val profile = ConnectStore(this@NeoConnectService).load() ?: error("Profil absent")
                val receiver = ReceiverCredentials(this@NeoConnectService).load()
                check(receiver.host == profile.receiverHost && receiver.port == profile.receiverPort)
                val config = Config.parse(profile.wireGuardConfig(packageName).byteInputStream())
                val engine = synchronized(guard) {
                    check(!destroyed)
                    (backend ?: GoBackend(applicationContext).also { backend = it }).also { it.setState(tunnel, Tunnel.State.UP, config) }
                }
                if (destroyed || !isActive) { disconnect(); return@launch }
                // A real packet initiates the exchange. A timeout is not called "connected".
                launch { runCatching { OpenWebif(receiver).ping() } }
                val server = Key.fromBase64(profile.serverPublicKey)
                while (isActive && !destroyed) {
                    val stats = synchronized(guard) {
                        check(engine.getState(tunnel) == Tunnel.State.UP)
                        engine.getStatistics(tunnel)
                    }
                    val handshake = stats.peer(server)?.latestHandshakeEpochMillis() ?: 0L
                    val recent = handshake > 0 && System.currentTimeMillis() - handshake in 0L..180000L
                    NeoConnect.mutable.value = ConnectStatus(if (recent) "connected" else "waiting",
                        if (recent) "Échange WireGuard authentifié. La lecture des chaînes reste à vérifier."
                        else "Aucun échange authentifié récent. Vérifier le Vu+, l’adresse Internet et UDP 51820.", stats.totalRx(), stats.totalTx())
                    delay(3000)
                }
            } catch (cancelled: CancellationException) {
                throw cancelled
            } catch (_: Exception) {
                disconnect()
                NeoConnect.mutable.value = ConnectStatus("error", "Tunnel indisponible. Vérifier le profil, les autorisations VPN et la configuration du Vu+.")
                stopSelf(startId)
            }
        }
        return START_NOT_STICKY // No silent reconnection or VPN takeover after process death.
    }

    private fun disconnect() {
        synchronized(guard) { runCatching { backend?.setState(tunnel, Tunnel.State.DOWN, null) } }
        if (NeoConnect.mutable.value.phase != "error") NeoConnect.mutable.value = ConnectStatus()
    }

    override fun onDestroy() {
        destroyed = true
        scope.cancel()
        Thread { disconnect() }.start()
        super.onDestroy()
    }
}
