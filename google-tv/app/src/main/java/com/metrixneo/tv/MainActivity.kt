package com.metrixneo.tv

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.media3.common.MediaItem
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.ui.PlayerView
import com.metrixneo.tv.data.Channel
import com.metrixneo.tv.data.OpenWebif
import com.metrixneo.tv.data.ReceiverSettings
import kotlinx.coroutines.launch

private object Neo {
    val bg = Color(0xFF061226)
    val navy = Color(0xF00B1D36)
    val azure = Color(0xFF1A8FFF)
    val cyan = Color(0xFF23CCFF)
    val white = Color(0xFFF2F8FF)
    val muted = Color(0xFF9AB2CF)
    val border = Color(0xFF25517B)
    val green = Color(0xFF55E9A7)
}
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                var page by remember { mutableStateOf("home") }
                var receiver by remember { mutableStateOf(ReceiverSettings()) }
                var channels by remember { mutableStateOf(emptyList<Channel>()) }
                var status by remember { mutableStateOf("Vu+ non connecté") }
                var loading by remember { mutableStateOf(false) }
                var selected by remember { mutableStateOf<Channel?>(null) }
                var url by remember { mutableStateOf<String?>(null) }
                var error by remember { mutableStateOf("") }
                val scope = rememberCoroutineScope()
                val client = remember(receiver) { OpenWebif(receiver) }
                fun goBack() { page = if (page == "player") "channels" else "home" }
                fun play(ch: Channel) {
                    selected = ch; url = null; error = "Recherche du flux…"; page = "player"
                    scope.launch {
                        try { url = client.stream(ch); error = "" }
                        catch (e: Exception) { error = e.message ?: "Flux indisponible" }
                    }
                }
                BackHandler(page != "home") { goBack() }
                Box(Modifier.fillMaxSize().background(
                    Brush.linearGradient(listOf(Color(0xFF092C53), Neo.bg, Color(0xFF020714)))
                )) {
                    Column(Modifier.fillMaxSize()) {
                        if (page != "player") {
                            Row(Modifier.fillMaxWidth().padding(horizontal = 26.dp, vertical = 12.dp),
                                verticalAlignment = Alignment.CenterVertically) {
                                Text("METRIX", color = Neo.white, fontSize = 25.sp, fontWeight = FontWeight.Black)
                                Text(" NEO", color = Neo.cyan, fontSize = 25.sp, fontWeight = FontWeight.Black)
                                Text(" AI", color = Color(0xFFB9A0FF), fontSize = 25.sp)
                                Spacer(Modifier.weight(1f))
                                Text(status, color = if (channels.isNotEmpty()) Neo.green else Neo.muted,
                                    fontSize = 12.sp)
                                Spacer(Modifier.width(16.dp))
                                Text("SONY BRAVIA  •  ANDROID TV", color = Neo.muted, fontSize = 11.sp)
                            }
                        }
                        Box(Modifier.weight(1f)) {
                            when (page) {
                                "home" -> HomeScreen({ page = it }, channels.isNotEmpty())
                                "channels" -> ChannelScreen(channels, ::play, { page = "settings" })
                                "guide" -> GuideScreen(channels, ::play)
                                "settings" -> SettingsScreen(receiver, status, loading) { config ->
                                    loading = true; status = "Connexion en cours"
                                    scope.launch {
                                        try {
                                            val api = OpenWebif(config)
                                            api.ping()
                                            val list = api.channels()
                                            if (list.isEmpty()) {
                                                status = "Vu+ accessible, mais aucun bouquet reçu"
                                            } else {
                                                receiver = config
                                                channels = list
                                                status = list.size.toString() + " chaînes synchronisées"
                                                page = "channels"
                                            }
                                        } catch (e: Exception) { status = e.message ?: "Erreur réseau" }
                                        loading = false
                                    }
                                }
                                "player" -> selected?.let { PlayerScreen(it, url, error) }
                                "ai" -> DiagnosticsScreen(status, channels.size)
                                else -> PlaceholderScreen { page = "home" }
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable private fun Panel(modifier: Modifier = Modifier, onClick: (() -> Unit)? = null,
    content: @Composable ColumnScope.() -> Unit) {
    var focused by remember { mutableStateOf(false) }
    val shape = RoundedCornerShape(14.dp)
    var m = modifier.clip(shape).background(
        if (focused) Color(0xFF165897) else Neo.navy
    ).border(if (focused) 2.dp else 1.dp, if (focused) Neo.cyan else Neo.border, shape)
    if (onClick != null) m = m.onFocusChanged { focused = it.isFocused }.clickable(onClick = onClick).focusable()
    Column(m.padding(17.dp), content = content)
}
@Composable private fun Heading(title: String, detail: String = "") {
    Text(title, color = Neo.white, fontSize = 23.sp, fontWeight = FontWeight.Bold)
    if (detail.isNotBlank()) Text(detail, color = Neo.muted, fontSize = 13.sp)
}
@Composable private fun Tile(symbol: String, name: String, detail: String, modifier: Modifier, onClick: () -> Unit) {
    Panel(modifier, onClick) {
        Spacer(Modifier.weight(1f))
        Text(symbol, color = Neo.cyan, fontSize = 43.sp)
        Spacer(Modifier.weight(1f))
        Text(name, color = Neo.white, fontSize = 18.sp, fontWeight = FontWeight.Bold)
        Text(detail, color = Neo.muted, fontSize = 11.sp, maxLines = 2)
    }
}
@Composable private fun HomeScreen(navigate: (String) -> Unit, linked: Boolean) {
    Column(Modifier.fillMaxSize().padding(horizontal = 26.dp, vertical = 13.dp)) {
        Text("L'EXPÉRIENCE TV INTELLIGENTE", color = Neo.cyan, fontSize = 11.sp, letterSpacing = 2.sp)
        Heading("Ton Metrix NEO, sur Sony BRAVIA", "Design bleu nuit • Navigation télécommande • TV via Vu+")
        Spacer(Modifier.height(21.dp))
        Row(Modifier.fillMaxWidth().weight(1f), horizontalArrangement = Arrangement.spacedBy(13.dp)) {
            Tile("▣", "TV en direct", "Chaînes SAT / IPTV", Modifier.weight(1f).fillMaxHeight()) { navigate("channels") }
            Tile("◉", "Bouquets", "Listes du Vu+", Modifier.weight(1f).fillMaxHeight()) { navigate("channels") }
            Tile("▦", "Guide TV", "EPG disponible", Modifier.weight(1f).fillMaxHeight()) { navigate("guide") }
            Tile("▶", "Enregistrements", "À développer", Modifier.weight(1f).fillMaxHeight()) { navigate("recordings") }
            Tile("⚙", "Paramètres", "Connexion Vu+", Modifier.weight(1f).fillMaxHeight()) { navigate("settings") }
        }
        Spacer(Modifier.height(14.dp))
        Row(Modifier.fillMaxWidth().weight(.75f), horizontalArrangement = Arrangement.spacedBy(13.dp)) {
            Panel(Modifier.weight(1f).fillMaxHeight(), { navigate("ai") }) {
                Heading("✦ METRIX NEO AI", "Fonctions intelligentes — feuille de route")
                Spacer(Modifier.height(15.dp))
                Text("Suggestions personnalisées : non disponibles en Alpha", color = Neo.muted, fontSize = 14.sp)
            }
            Panel(Modifier.weight(1f).fillMaxHeight(), { navigate("channels") }) {
                Heading("Continuer à regarder")
                Spacer(Modifier.height(15.dp))
                Text(if (linked) "Bouquets Vu+ synchronisés" else "Configure le Vu+ pour commencer",
                    color = Neo.cyan, fontSize = 17.sp)
            }
            Panel(Modifier.weight(1f).fillMaxHeight(), { navigate("ai") }) {
                Heading("Diagnostic local")
                Spacer(Modifier.height(15.dp))
                Text(if (linked) "● Récepteur accessible" else "● En attente de connexion",
                    color = if (linked) Neo.green else Neo.muted, fontSize = 16.sp)
            }
        }
        Text("METRIX NEO AI  •  VERSION ALPHA 0.3  •  OK : OUVRIR  •  RETOUR : ACCUEIL",
            color = Neo.muted, fontSize = 10.sp, modifier = Modifier.padding(top = 12.dp))
    }
}
@Composable private fun ChannelScreen(channels: List<Channel>, play: (Channel) -> Unit, settings: () -> Unit) {
    Column(Modifier.fillMaxSize().padding(24.dp)) {
        Heading("Liste des chaînes", if (channels.isEmpty()) "Connecte le Vu+ dans Paramètres" else channels.size.toString() + " services OpenWebif")
        Spacer(Modifier.height(12.dp))
        if (channels.isEmpty()) {
            Panel(Modifier.fillMaxWidth(), settings) { Text("Ouvrir la configuration Vu+  →", color = Neo.cyan, fontSize = 19.sp) }
        } else LazyColumn(verticalArrangement = Arrangement.spacedBy(5.dp)) {
            itemsIndexed(channels) { index, ch ->
                Panel(Modifier.fillMaxWidth(), { play(ch) }) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text("%04d".format(index + 1), color = Neo.cyan, modifier = Modifier.width(68.dp))
                        Text(ch.name, color = Neo.white, fontSize = 16.sp, modifier = Modifier.weight(1f),
                            maxLines = 1, overflow = TextOverflow.Ellipsis)
                        Text(ch.current.ifBlank { ch.bouquet }, color = Neo.muted, fontSize = 13.sp,
                            modifier = Modifier.weight(.85f), maxLines = 1)
                    }
                }
            }
        }
    }
}
@Composable private fun GuideScreen(channels: List<Channel>, play: (Channel) -> Unit) {
    Column(Modifier.fillMaxSize().padding(24.dp)) {
        Heading("Guide TV • EPG", "Affiche uniquement les programmes renvoyés par OpenWebif")
        Spacer(Modifier.height(12.dp))
        LazyColumn(verticalArrangement = Arrangement.spacedBy(5.dp)) {
            itemsIndexed(channels) { _, ch ->
                Panel(Modifier.fillMaxWidth(), { play(ch) }) {
                    Row {
                        Text(ch.name, color = Neo.white, modifier = Modifier.weight(1f))
                        Text(ch.current.ifBlank { "EPG indisponible" }, color = Neo.cyan, modifier = Modifier.weight(2f))
                        Text(ch.next.ifBlank { "Suivant non disponible" }, color = Neo.muted, modifier = Modifier.weight(2f))
                    }
                }
            }
        }
    }
}
@Composable private fun SettingsScreen(initial: ReceiverSettings, status: String, busy: Boolean,
    connect: (ReceiverSettings) -> Unit) {
    var host by remember { mutableStateOf(initial.host) }
    var port by remember { mutableStateOf(initial.port.toString()) }
    var username by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    Column(Modifier.fillMaxSize().padding(32.dp)) {
        Heading("Connexion Vu+ Zero 4K", "OpenATV 8.0.1 • OpenWebif lecture seule • réseau local uniquement")
        Spacer(Modifier.height(20.dp))
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(24.dp)) {
            OutlinedTextField(host, { host = it }, label = { Text("IP Vu+ (pas IP Sony)") }, modifier = Modifier.weight(1f))
            OutlinedTextField(port, { port = it }, label = { Text("Port OpenWebif") }, modifier = Modifier.weight(1f))
        }
        Spacer(Modifier.height(12.dp))
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(24.dp)) {
            OutlinedTextField(username, { username = it }, label = { Text("Utilisateur (optionnel)") }, modifier = Modifier.weight(1f))
            OutlinedTextField(password, { password = it }, label = { Text("Mot de passe (non enregistré)") }, modifier = Modifier.weight(1f))
        }
        Spacer(Modifier.height(17.dp))
        Button(enabled = !busy && port.toIntOrNull() in 1..65535, onClick = {
            connect(ReceiverSettings(host.trim(), port.toInt(), username, password))
        }) { Text(if (busy) "Connexion…" else "Tester et charger les bouquets") }
        Spacer(Modifier.height(16.dp))
        Text(status, color = Neo.cyan)
        Text("Sony : 192.168.11.188 • Cible ADB uniquement, jamais une adresse OpenWebif.",
            color = Neo.muted, fontSize = 12.sp, modifier = Modifier.padding(top = 12.dp))
    }
}
@Composable private fun PlayerScreen(ch: Channel, url: String?, message: String) {
    val context = LocalContext.current
    val player = remember(url) {
        if (url.isNullOrBlank()) null else ExoPlayer.Builder(context).build().apply {
            setMediaItem(MediaItem.fromUri(url))
            prepare()
            playWhenReady = true
        }
    }
    DisposableEffect(player) { onDispose { player?.release() } }
    Box(Modifier.fillMaxSize().background(Color.Black)) {
        if (player != null)
            AndroidView(factory = { PlayerView(it).apply { this.player = player; useController = false } },
                modifier = Modifier.fillMaxSize())
        else Text(message, color = Neo.white, modifier = Modifier.align(Alignment.Center))
        Panel(Modifier.align(Alignment.BottomCenter).fillMaxWidth().padding(20.dp)) {
            Text(ch.name, color = Neo.white, fontSize = 23.sp, fontWeight = FontWeight.Bold)
            Text(ch.current.ifBlank { "Émission actuelle : EPG indisponible" }, color = Neo.cyan, fontSize = 16.sp)
            Text("Suivant : " + ch.next.ifBlank { "non disponible" }, color = Neo.muted, fontSize = 12.sp)
            Spacer(Modifier.height(8.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                listOf("UHD","HDR","HEVC","DOLBY","AC3","16:9","TXT","SUB","AUD","REC","SAT","IPTV","SNR","AGC").forEach {
                    Text(it, color = Neo.muted, fontSize = 10.sp,
                        modifier = Modifier.border(1.dp, Neo.border, RoundedCornerShape(3.dp))
                            .padding(horizontal = 7.dp, vertical = 4.dp))
                }
            }
            Text("14 indicateurs : état réel à intégrer • RETOUR pour les chaînes",
                color = Neo.muted, fontSize = 10.sp, modifier = Modifier.padding(top = 8.dp))
        }
    }
}
@Composable private fun DiagnosticsScreen(status: String, count: Int) {
    Column(Modifier.fillMaxSize().padding(30.dp)) {
        Heading("Metrix NEO AI — Diagnostic", "Mesures réelles uniquement, sans fonctions IA simulées")
        Spacer(Modifier.height(25.dp))
        Panel(Modifier.fillMaxWidth()) {
            Text(status, color = Neo.cyan, fontSize = 20.sp)
            Text("Chaînes synchronisées : " + count, color = Neo.white)
            Text("Optimisation de zapping / recommandations locales : à développer après tests sur la Sony",
                color = Neo.muted, modifier = Modifier.padding(top = 18.dp))
        }
    }
}
@Composable private fun PlaceholderScreen(back: () -> Unit) {
    Column(Modifier.fillMaxSize().padding(30.dp)) {
        Heading("Module à développer", "Cette fonction n'est pas disponible dans la préversion.")
        Spacer(Modifier.height(20.dp))
        Button(onClick = back) { Text("Retour à l'accueil") }
    }
}
