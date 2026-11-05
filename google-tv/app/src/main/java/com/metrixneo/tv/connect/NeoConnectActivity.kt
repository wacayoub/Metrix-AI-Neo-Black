package com.metrixneo.tv.connect

import android.content.Intent
import android.net.VpnService
import android.os.Build
import android.os.Bundle
import android.os.SystemClock
import android.view.KeyEvent
import android.view.WindowManager
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.testTagsAsResourceId
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.metrixneo.tv.ReceiverCredentials
import com.metrixneo.tv.MainActivity
import com.metrixneo.tv.data.OpenWebif
import com.wireguard.android.backend.GoBackend
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class NeoConnectActivity : ComponentActivity() {
    private var firstBackAt = -1L
    private var permissionMessage by mutableStateOf("")
    private val vpnPermission = registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
        if (result.resultCode == RESULT_OK) NeoConnect.start(this)
        else permissionMessage = "Autorisation VPN refusée. Le tunnel reste arrêté."
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        NeoConnect.returnBackAt = -1L
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        setContent {
            BackHandler { returnFromBack() }
            MaterialTheme(colorScheme = darkColorScheme(primary = Color(0xFF11B8EF), background = Color(0xFF031323))) {
                Surface(Modifier.fillMaxSize().semantics { testTagsAsResourceId = true }.testTag("neo.connect")) { Content() }
            }
        }
    }

    private fun returnFromBack() {
        val now = SystemClock.elapsedRealtime()
        if (firstBackAt >= 0L && now - firstBackAt in 0L..2000L) {
            if (!MainActivity.exitFromConnect()) {
                startActivity(Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_HOME).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
                finishAndRemoveTask()
            }
            return
        }
        firstBackAt = now
        NeoConnect.returnBackAt = now
        Toast.makeText(this, "Encore une fois sur EXIT / Retour pour quitter", Toast.LENGTH_SHORT).show()
        finish()
    }

    override fun onKeyDown(keyCode: Int, event: KeyEvent): Boolean {
        if (keyCode == KeyEvent.KEYCODE_ESCAPE) {
            if (event.repeatCount == 0) returnFromBack()
            return true
        }
        return super.onKeyDown(keyCode, event)
    }

    @Composable private fun Content() {
        val scope = rememberCoroutineScope()
        val store = remember { ConnectStore(this) }
        val receiver = remember { ReceiverCredentials(this).load() }
        val client = remember { PairingClient() }
        var fingerprint by remember { mutableStateOf("") }
        var confirmed by remember { mutableStateOf(false) }
        var code by remember { mutableStateOf("") }
        var name by remember { mutableStateOf(Build.MODEL.take(40).replace(Regex("[^\\p{L}\\p{N}_ .-]"), "_")) }
        var busy by remember { mutableStateOf(false) }
        var paired by remember { mutableStateOf(store.exists()) }
        var message by remember { mutableStateOf("Sur le Vu+ : ouvrir Neo Connect, puis activer l’association. Les deux appareils doivent être sur le même réseau local.") }
        val status by NeoConnect.status.collectAsState()
        var forget by remember { mutableStateOf(false) }
        var endpoint by remember { mutableStateOf("") }
        var engineReady by remember { mutableStateOf(false) }
        var engineMessage by remember { mutableStateOf("Vérification du moteur intégré…") }
        val stopped = status.phase in listOf("off", "error")
        LaunchedEffect(Unit) {
            try {
                val version = withContext(Dispatchers.IO) { GoBackend(applicationContext).version }
                engineReady = version.isNotBlank()
                engineMessage = if (engineReady) "Moteur intégré chargé. Aucun tunnel démarré automatiquement." else "Moteur intégré indisponible."
            } catch (_: Exception) { engineMessage = "Moteur intégré indisponible sur cet appareil." }
              catch (_: LinkageError) { engineMessage = "Moteur intégré incompatible avec cet appareil." }
        }
        LaunchedEffect(paired) {
            if (paired) {
                try { endpoint = withContext(Dispatchers.IO) { store.load()?.endpoint.orEmpty() } }
                catch (_: Exception) { message = "Profil local illisible. Oublier cet appareil puis refaire l’association." }
            }
        }

        fun operation(failure: String, action: suspend () -> String) {
            busy = true; permissionMessage = ""
            scope.launch {
                message = try { action() } catch (cancelled: CancellationException) { throw cancelled } catch (_: Exception) { failure }
                paired = store.exists(); busy = false
            }
        }

        Column(Modifier.fillMaxSize().padding(32.dp).verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(16.dp)) {
            Text("Neo Connect", fontSize = 30.sp)
            Text("Connexion privée intégrée • sans compte cloud • Vu+ ${receiver.host}:${receiver.port}", fontSize = 18.sp)
            Text(engineMessage, modifier = Modifier.testTag("neo.connect.engine"), fontSize = 16.sp)
            Text(status.message, modifier = Modifier.testTag("neo.connect.status"), color = MaterialTheme.colorScheme.primary, fontSize = 18.sp)
            if (!paired) {
                Button(enabled = !busy && stopped && engineReady && privateV4(receiver.host), modifier = Modifier.testTag("neo.connect.discover"), onClick = {
                    fingerprint = ""; confirmed = false
                    operation("Association locale indisponible. Vérifier que le plugin est activé sur le Vu+ et que son port HTTPS 9843 est accessible.") {
                        fingerprint = withContext(Dispatchers.IO) { client.discover(receiver.host) }
                        "Comparer l’empreinte ci-dessous à celle affichée sur le Vu+."
                    }
                }) { Text("1. Lire l’empreinte du Vu+") }
                if (fingerprint.isNotEmpty()) {
                    Text("SHA-256 : " + fingerprint.chunked(8).joinToString(" "), fontSize = 20.sp, modifier = Modifier.testTag("neo.connect.fingerprint"))
                    Row {
                        Checkbox(checked = confirmed, onCheckedChange = { confirmed = it }, modifier = Modifier.testTag("neo.connect.confirm"))
                        Text("L’empreinte correspond exactement à celle affichée sur mon Vu+", Modifier.padding(top = 12.dp))
                    }
                    OutlinedTextField(name, { name = it.take(40) }, label = { Text("Nom de cet appareil") }, singleLine = true)
                    OutlinedTextField(code, { code = it.filter { character -> character in '0'..'9' }.take(6) }, label = { Text("Code de 6 chiffres affiché sur le Vu+") },
                        visualTransformation = PasswordVisualTransformation(), singleLine = true, modifier = Modifier.testTag("neo.connect.code"))
                    Button(enabled = !busy && confirmed && code.length == 6 && stopped, modifier = Modifier.testTag("neo.connect.pair"), onClick = {
                        val pin = fingerprint; val otp = code; val label = name
                        code = ""
                        operation("Association refusée. Vérifier l’empreinte et renouveler le code sur le Vu+. Aucun profil actif.") {
                            withContext(Dispatchers.IO) {
                                val profile = client.pair(receiver.host, receiver.port, pin, otp, label)
                                store.save(profile)
                            }
                            "Appareil associé. La clé privée est chiffrée sur cette TV. La connexion 4G/5G reste à tester."
                        }
                    }) { Text("2. Associer cet appareil") }
                }
            } else {
                Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                    OutlinedTextField(endpoint, { endpoint = it.take(260) }, enabled = stopped && !busy,
                        label = { Text("Adresse Internet du Vu+ : hôte:port") }, singleLine = true, modifier = Modifier.weight(1f))
                    OutlinedButton(enabled = stopped && !busy, onClick = {
                        val value = endpoint
                        operation("Adresse refusée ou profil illisible. Utiliser hôte:port ou [IPv6]:port.") {
                            withContext(Dispatchers.IO) { store.save(requireNotNull(store.load()).withEndpoint(value)) }
                            "Adresse Internet enregistrée ; les clés d’association restent identiques."
                        }
                    }) { Text("Enregistrer l’adresse") }
                }
                Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                    Button(enabled = !busy && stopped && engineReady, modifier = Modifier.testTag("neo.connect.start"), onClick = {
                        permissionMessage = ""
                        val permission = VpnService.prepare(this@NeoConnectActivity)
                        if (permission == null) NeoConnect.start(this@NeoConnectActivity) else vpnPermission.launch(permission)
                    }) { Text("Connecter") }
                    Button(enabled = !busy && !stopped, modifier = Modifier.testTag("neo.connect.stop"), onClick = { NeoConnect.stop(this@NeoConnectActivity) }) { Text("Déconnecter") }
                    OutlinedButton(enabled = !busy && stopped, onClick = { forget = true }) { Text("Oublier cet appareil") }
                }
                Text("Reçu : ${status.rx} octets • Envoyé : ${status.tx} octets", fontSize = 16.sp)
                Button(enabled = !busy && status.phase == "connected", modifier = Modifier.testTag("neo.connect.test"), onClick = {
                    operation("Le tunnel est lancé mais OpenWebif ne répond pas. Vérifier sa disponibilité et ses identifiants dans Setup.") {
                        withContext(Dispatchers.IO) { OpenWebif(receiver).ping() }
                        "OpenWebif a répondu dans le tunnel. Tester maintenant une chaîne ; la disponibilité du tuner reste nécessaire."
                    }
                }) { Text("Tester l’accès au Vu+") }
            }
            if (busy) LinearProgressIndicator(Modifier.fillMaxWidth())
            Text(message, fontSize = 18.sp, modifier = Modifier.testTag("neo.connect.message"))
            if (permissionMessage.isNotEmpty()) Text(permissionMessage, color = MaterialTheme.colorScheme.error)
            Text("Sur Internet, prévoir une adresse joignable et UDP 51820 vers le Vu+. Ne pas ouvrir OpenWebif ni le port d’association 9843. Un autre VPN actif sera remplacé après votre autorisation Android.", fontSize = 16.sp)
            OutlinedButton(onClick = { finish() }, modifier = Modifier.testTag("neo.connect.back")) { Text("Retour à Neo") }
        }
        if (forget) AlertDialog(onDismissRequest = { forget = false }, title = { Text("Oublier le profil local ?") },
            text = { Text("Révoquer aussi cet appareil depuis le plugin Vu+ pour supprimer son autorisation sur le serveur.") },
            confirmButton = { TextButton(onClick = {
                forget = false
                operation("Suppression locale impossible.") { withContext(Dispatchers.IO) { store.clear() }; fingerprint = ""; confirmed = false; "Profil local supprimé." }
            }) { Text("Oublier") } }, dismissButton = { TextButton(onClick = { forget = false }) { Text("Annuler") } })
    }
}
