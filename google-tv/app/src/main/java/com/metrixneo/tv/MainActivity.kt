package com.metrixneo.tv

import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.os.Bundle
import android.os.SystemClock
import android.util.Log
import android.view.KeyEvent
import android.view.KeyEvent.*
import android.view.WindowManager
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.selected
import androidx.compose.ui.semantics.stateDescription
import androidx.compose.ui.semantics.testTagsAsResourceId
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.input.key.onPreviewKeyEvent
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.media3.common.*
import androidx.media3.datasource.DefaultHttpDataSource
import androidx.media3.datasource.DataSource
import androidx.media3.exoplayer.upstream.DefaultLoadErrorHandlingPolicy
import androidx.media3.exoplayer.upstream.LoadErrorHandlingPolicy
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.exoplayer.source.DefaultMediaSourceFactory
import androidx.media3.ui.PlayerView
import com.metrixneo.tv.data.Channel
import com.metrixneo.tv.data.ChannelCatalog
import com.metrixneo.tv.data.ResumeFolder
import com.metrixneo.tv.data.ResumeSource
import com.metrixneo.tv.data.ResumeState
import com.metrixneo.tv.data.restoredIndex
import com.metrixneo.tv.data.pageWindow
import com.metrixneo.tv.data.OpenWebif
import com.metrixneo.tv.data.Programme
import com.metrixneo.tv.data.ReceiverSettings
import com.metrixneo.tv.data.Satellite
import com.metrixneo.tv.data.ServiceEntry
import com.metrixneo.tv.data.isDirectoryRef
import com.metrixneo.tv.data.usesReceiverAuthentication
import com.metrixneo.tv.data.ReceiverStreamDataSource
import com.metrixneo.tv.data.ReceiverStreamException
import com.metrixneo.tv.data.PiconStore
import com.metrixneo.tv.data.ChannelStore
import com.metrixneo.tv.data.Weather
import com.metrixneo.tv.data.WeatherInfo
import com.metrixneo.tv.playback.GStreamerPlayer
import com.metrixneo.tv.playback.AdaptiveLoadControl
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.flow.debounce
import kotlinx.coroutines.sync.Semaphore
import kotlinx.coroutines.sync.withPermit
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

private object Neo {
    val bg = Color(0xFF031323); val panel = Color(0xFF031523)
    val white = Color(0xFFE9F0F8); val muted = Color(0xFFA7B6C8)
    val cyan = Color(0xFF11B8EF); val epg = Color(0xFF48A6CC); val line = Color(0xFF123E5A)
    val track = Color(0xFF1D2E3E)
    val colors = listOf(Color(0xFFF02C2C), Color(0xFF23CD38), Color(0xFFF2D936), Color(0xFF119BE6))
}

class MainActivity : ComponentActivity() {
    companion object {
        private var current = java.lang.ref.WeakReference<MainActivity>(null)
        internal fun exitFromConnect(): Boolean {
            val activity = current.get() ?: return false
            activity.exitToHome()
            return true
        }
    }
    private var activeUi: ReceiverUi? = null
    private var exitPressedAt = -1L
    private var exitHint: Toast? = null
    private fun resetExit() { exitPressedAt = -1L; exitHint?.cancel(); exitHint = null }
    private var wasStopped = false
    private fun exitToHome() {
        resetExit(); activeUi?.pausePlayback()
        Log.i("NeoExit", "home_requested")
        startActivity(Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_HOME).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
        finishAndRemoveTask()
    }
    override fun onResume() {
        super.onResume(); resetExit()
        val returned = com.metrixneo.tv.connect.NeoConnect.returnBackAt
        com.metrixneo.tv.connect.NeoConnect.returnBackAt = -1L
        if (returned >= 0L && SystemClock.elapsedRealtime() - returned in 0L..2000L) exitPressedAt = returned
        if (wasStopped) activeUi?.onForeground()
        wasStopped = false
    }
    override fun onStop() { resetExit(); wasStopped = true; activeUi?.onBackground(); super.onStop() }
    private fun exitOrBack() {
        val ui = activeUi ?: return
        val now = SystemClock.elapsedRealtime()
        if (exitPressedAt >= 0L && now - exitPressedAt in 0L..2000L) {
            exitToHome()
        } else {
            exitPressedAt = now
            ui.back()
            exitHint?.cancel()
            exitHint = Toast.makeText(this, "Encore une fois sur EXIT / Retour pour quitter", Toast.LENGTH_SHORT).also { it.show() }
            Log.i("NeoExit", "back_first")
        }
    }
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        current = java.lang.ref.WeakReference(this)
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        setContent {
            val scope = rememberCoroutineScope()
            val ui = remember { ReceiverUi(this, scope, onExit = ::exitOrBack, onInteraction = ::resetExit) }
            SideEffect { activeUi = ui }
            DisposableEffect(Unit) { onDispose { activeUi = null; ui.releasePlayback() } }
            LaunchedEffect(Unit) { ui.connect(ui.settings, restore = true); ui.startWeather() }
            BackHandler { exitOrBack() }
            MaterialTheme(colorScheme = darkColorScheme(primary = Neo.cyan, background = Neo.bg, surface = Neo.panel)) { Screen(ui) }
        }
    }
    override fun onDestroy() {
        if (current.get() === this) current.clear()
        super.onDestroy()
    }
}

private data class Meta(val events: List<Programme>, val icon: Bitmap?, val fetched: Long)
private data class FolderFrame(val title: String, val ref: String?, val entries: List<ServiceEntry>, val index: Int)
private data class ResumeContents(val channels: List<Channel>, val entries: List<ServiceEntry> = emptyList(), val parents: List<FolderFrame> = emptyList())
private val LocalWeather = staticCompositionLocalOf<WeatherInfo?> { null }
@androidx.annotation.OptIn(androidx.media3.common.util.UnstableApi::class)
private class ReceiverUi(val context: Context, val scope: CoroutineScope, val onExit: () -> Unit, val onInteraction: () -> Unit) {
    private val prefs = context.getSharedPreferences("receiver", Context.MODE_PRIVATE)
    var listMiniTv by mutableStateOf(prefs.getBoolean("channel_list_mini_tv", true))
        private set
    fun toggleListVideo() {
        listMiniTv = !listMiniTv
        prefs.edit().putBoolean("channel_list_mini_tv", listMiniTv).apply()
    }
    private val credentials = ReceiverCredentials(context)
    private val resumeStore = ResumeStore(context)
    private var navigationKind by mutableStateOf("bouquet")
    private var satelliteRef: String? = null
    private var playingSource by mutableStateOf<ResumeSource?>(null)
    private var previousSource: ResumeSource? = null
    private var startupPending = true
    private var resumeUnresolved = false
    private var resumeGeneration = 0
    private var sessionReady by mutableStateOf(false)
    private var restoreSelectionOnNextList = false
    private val appVersion = context.packageManager.getPackageInfo(context.packageName, 0).versionName.orEmpty()
    val engines = listOf("Media3", "GStreamer")
    var engine by mutableStateOf(prefs.getString("player_engine", "Media3").takeIf { it in engines } ?: "Media3")
        private set
    var gstReady by mutableStateOf(false)
    var gstPlaying by mutableStateOf(false)
    private var gstVideo by mutableStateOf<Format?>(null)
    private var gstAudioTracks by mutableIntStateOf(0)
    private var gstTextTracks by mutableIntStateOf(0)
    private var gstAudioSelected by mutableIntStateOf(0)
    private var gstTextSelected by mutableIntStateOf(-1)
    private var gstInstance: GStreamerPlayer? = null
    fun gstPlayer(): GStreamerPlayer = gstInstance ?: GStreamerPlayer(context) { kind, id, detail, width, height ->
        if (engine == "GStreamer" && id == zapSequence) {
            when (kind) {
                2 -> { gstReady = true; gstPlaying = true; playbackMessage = "" }
                3 -> { gstReady = false; playbackMessage = detail }
                4, 5 -> { gstReady = false; gstPlaying = false; playbackFailed = true; playbackMessage = "$detail  OK : réessayer."; banner = true }
                6, 7 -> {
                    if (kind == 7) { gstReady = true; gstPlaying = true; playbackMessage = "" }
                    gstVideo = if (width > 0 && height > 0) Format.Builder().setWidth(width).setHeight(height).build() else null
                    val counts = detail.split(':'); gstAudioTracks = counts.getOrNull(0)?.toIntOrNull() ?: 0
                    gstTextTracks = counts.getOrNull(1)?.toIntOrNull() ?: 0
                    Log.i("NeoGst", "${if (kind == 7) "video_frame" else "video_format"} id=$id elapsed_ms=${SystemClock.elapsedRealtime() - zapStartedAt} width=$width height=$height audio=$gstAudioTracks text=$gstTextTracks")
                    if (kind == 7) afterFirstFrame(id)
                }
                8 -> gstPlaying = false
            }
            if (kind !in listOf(6, 7)) Log.i("NeoGst", "event id=$id kind=$kind")
        }
    }.also { gstInstance = it }
    val videoFormat get() = if (engine != "Media3") gstVideo else player.videoFormat
    val audioFormat get() = if (engine != "Media3") null else player.audioFormat
    private val playbackReady get() = if (engine != "Media3") gstReady else player.playbackState == Player.STATE_READY
    private val isPlaybackPlaying get() = if (engine != "Media3") gstPlaying else player.isPlaying
    fun pausePlayback() { if (engine == "GStreamer") { gstInstance?.pause(); gstPlaying = false } else player.pause() }
    fun resumePlayback() {
        if (playbackFailed) { playing?.let { play(it, force = true) }; return }
        if (engine == "GStreamer") { gstInstance?.play(); gstPlaying = true } else player.play()
    }
    fun releasePlayback() { playbackMonitor?.cancel(); gstInstance?.release(); player.release() }
    fun selectEngine(value: String) {
        if (value == engine || value !in engines) return
        tuneJob?.cancel(); afterFrameJob?.cancel()
        player.stop(); gstInstance?.stop(); gstReady = false; gstPlaying = false
        engine = value; prefs.edit().putString("player_engine", value).apply()
        playing?.let { val previousPage = page; play(it); page = previousPage }
    }
    var settings by mutableStateOf(credentials.load())
    private var receiverApi = OpenWebif(settings)
    private var mediaFactory = createMediaFactory(settings)
    private val internetMediaFactory = createMediaFactory(settings, receiverAuth = false)
    var page by mutableStateOf("channels")
    var channels by mutableStateOf<List<Channel>>(emptyList())
    var bouquet by mutableStateOf(prefs.getString("bouquet", "")!!)
    var index by mutableIntStateOf(0)
    var bouquetIndex by mutableIntStateOf(0)
    var satellites by mutableStateOf<List<Satellite>>(emptyList())
    var satelliteName by mutableStateOf("")
    var satelliteServices by mutableStateOf<List<Channel>>(emptyList())
    var folderTitle by mutableStateOf("Bouquets TV")
    var folderEntries by mutableStateOf<List<ServiceEntry>>(emptyList())
    var folderIndex by mutableIntStateOf(0)
    var folderBusy by mutableStateOf(false)
    var folderPlayback by mutableStateOf(false)
    private var folderPlaybackTitle by mutableStateOf("")
    private var folderChannels by mutableStateOf<List<Channel>>(emptyList())
    private var folderRef: String? = null
    private val folderHistory = java.util.ArrayDeque<FolderFrame>()
    private val folderCache = object : LinkedHashMap<String, List<ServiceEntry>>(32, .75f, true) {
        override fun removeEldestEntry(eldest: MutableMap.MutableEntry<String, List<ServiceEntry>>?) = size > 32
    }
    private var folderJob: Job? = null
    private var folderGeneration = 0
    var weather by mutableStateOf<WeatherInfo?>(null)
    private val picons = PiconStore(context)
    private val channelStore = ChannelStore(context)
    private val iconPermits = Semaphore(2)
    private val loadingIcons = HashSet<String>()
    private val loadingMeta = HashSet<String>()
    private val satelliteCache = object : LinkedHashMap<String, List<Channel>>(8, .75f, true) {
        override fun removeEldestEntry(eldest: MutableMap.MutableEntry<String, List<Channel>>?) = size > 8
    }
    private var satelliteJob: Job? = null
    private var satelliteGeneration = 0
    var menuIndex by mutableIntStateOf(0)
    var detailIndex by mutableIntStateOf(0)
    var status by mutableStateOf("Connexion au Vu+…")
    var busy by mutableStateOf(false)
    var playing by mutableStateOf<Channel?>(null)
    private var previous: Channel? = null
    var playbackMessage by mutableStateOf("")
    var banner by mutableStateOf(true)
    var number by mutableStateOf("")
    var messageTitle by mutableStateOf("")
    var messageBody by mutableStateOf("")
    var information by mutableStateOf("")
    val meta = mutableStateMapOf<String, Meta>()
    private val permits = Semaphore(2)
    private val selectedMetaPermit = Semaphore(1)
    private var tuneJob: Job? = null
    private var bannerJob: Job? = null
    private var numberJob: Job? = null
    private var afterFrameJob: Job? = null
    private var playbackMonitor: Job? = null
    private var zapSequence = 0L
    private var zapStartedAt = 0L
    private var renderedSequence = -1L
    var playbackFailed by mutableStateOf(false)
        private set
    val player = ExoPlayer.Builder(context).setLoadControl(AdaptiveLoadControl()).build().apply {
        addListener(object : Player.Listener {
            override fun onIsPlayingChanged(isPlaying: Boolean) {
                if (engine == "Media3") Log.i("NeoZap", "playing id=${currentMediaItem?.mediaId} value=$isPlaying")
            }
            override fun onRenderedFirstFrame() {
                if (engine == "Media3" && currentMediaItem?.mediaId == zapSequence.toString() && renderedSequence != zapSequence) {
                    renderedSequence = zapSequence
                    Log.i("NeoZap", "first_frame id=$zapSequence elapsed_ms=${SystemClock.elapsedRealtime() - zapStartedAt}")
                    afterFirstFrame(zapSequence)
                }
            }
            override fun onPlayerError(error: PlaybackException) {
                if (engine != "Media3") return
                Log.i("NeoZap", "error id=$zapSequence code=${error.errorCodeName}")
                playbackFailed = true
                val receiverError = generateSequence(error as Throwable?) { it.cause }.filterIsInstance<ReceiverStreamException>().firstOrNull()
                val http = generateSequence(error as Throwable?) { it.cause }
                    .filterIsInstance<androidx.media3.datasource.HttpDataSource.InvalidResponseCodeException>().firstOrNull()
                playbackMessage = when {
                    receiverError != null -> "Le Vu+ refuse d’ouvrir cette chaîne (HTTP ${receiverError.statusCode}). Tuner occupé ou service indisponible : mets le Vu+ en veille simple, puis OK pour réessayer."
                    http?.responseCode in listOf(401, 403) -> "Le serveur du flux refuse l’accès (HTTP ${http?.responseCode}). Vérifie les identifiants ou la validité de l’abonnement. OK : réessayer."
                    http?.responseCode == 404 -> "Cette chaîne n’est plus disponible (HTTP 404). OK : réessayer."
                    error.errorCode == PlaybackException.ERROR_CODE_PARSING_CONTAINER_UNSUPPORTED -> "Le serveur n’a pas fourni une vidéo reconnue. OK : réessayer."
                    else -> "Lecture impossible : ${error.errorCodeName}. OK : réessayer."
                }; banner = true
            }
            override fun onPlaybackStateChanged(state: Int) {
                if (engine != "Media3") return
                Log.i("NeoZap", "state id=${currentMediaItem?.mediaId} value=$state elapsed_ms=${SystemClock.elapsedRealtime() - zapStartedAt}")
                if (state == Player.STATE_READY) { playbackMessage = ""; playbackFailed = false }
                if (state == Player.STATE_BUFFERING) playbackMessage = "Mise en mémoire tampon…"
            }
        })
    }
    // Derived once per source/filter change, not once per row or remote key.
    private val catalog by derivedStateOf { ChannelCatalog(channels) }
    val bouquets get() = catalog.names
    fun bouquetSize(name: String) = catalog.count(name)
    val visible by derivedStateOf { if (folderPlayback) folderChannels else if (satelliteName.isNotBlank()) satelliteServices else if (bouquet.isBlank()) catalog.all else catalog.bouquet(bouquet) }
    val listTitle get() = if (folderPlayback) folderPlaybackTitle else satelliteName.ifBlank { bouquet.ifBlank { "Tous les services" } }
    val selected get() = visible.getOrNull(index)
    val pageStart by derivedStateOf { index / 20 * 20 }
    private fun currentSource(): ResumeSource = when (navigationKind) {
        "folder" -> ResumeSource("folder", folderTitle, folderRef, folderHistory.map { ResumeFolder(it.title, it.ref, it.index) })
        "satellite" -> ResumeSource("satellite", satelliteName, satelliteRef)
        else -> if (bouquet.isBlank()) ResumeSource("all") else ResumeSource("bouquet", bouquet)
    }
    fun resumeSnapshot(): ResumeState? {
        if (!sessionReady) return null
        val source = currentSource()
        val folders = source.kind == "folder" && !folderPlayback
        if (folders && (folderBusy || folderEntries.isEmpty())) return null
        if (!folders && visible.isEmpty()) return null
        return ResumeState(source, if (folders) folderEntries.getOrNull(folderIndex)?.ref else selected?.ref,
            if (folders) folderIndex else index,
            if (folders) "folders" else if (playing != null && page != "channels") "player" else "channels", playing, playingSource)
    }
    suspend fun persistResume(state: ResumeState, config: ReceiverSettings) {
        if (settings != config) return
        val request = resumeStore.nextGeneration()
        withContext(Dispatchers.IO) { resumeStore.write(config, state, request) }
    }
    private fun saveResumeNow() {
        val snapshot = resumeSnapshot() ?: return
        resumeStore.write(settings, snapshot, resumeStore.nextGeneration())
    }
    private fun cancelStartupResume() {
        if (startupPending || resumeUnresolved) {
            startupPending = false; resumeUnresolved = false; resumeGeneration++; sessionReady = true
            Log.i("NeoResume", "cancelled_by_interaction")
        }
    }
    fun onBackground() { val ready = sessionReady; cancelStartupResume(); if (ready) saveResumeNow(); pausePlayback() }
    fun onForeground() {
        playing?.let { ch ->
            val oldPage = page; val oldIndex = index
            play(ch, restoring = true, force = true); index = oldIndex; page = oldPage
        }
    }
    private suspend fun restoreResume(saved: ResumeState, api: OpenWebif, generation: Int) {
        val loaded = HashMap<String, ResumeContents>()
        suspend fun resolve(source: ResumeSource, history: Boolean): ResumeContents {
            val key = "${source.kind}:${source.ref}:${source.name}:$history"
            loaded[key]?.let { return it }
            val result = when (source.kind) {
                "all" -> ResumeContents(catalog.all)
                "bouquet" -> ResumeContents(catalog.bouquet(source.name))
                "satellite" -> {
                    val satellite = api.satellites().firstOrNull { it.ref == source.ref }
                    ResumeContents(if (satellite == null) emptyList() else api.satelliteChannels(satellite))
                }
                "folder" -> {
                    val entries = api.entries(source.ref)
                    val parents = if (!history) emptyList() else source.parents.map { f ->
                        FolderFrame(f.title, f.ref, api.entries(f.ref), f.index)
                    }
                    ResumeContents(entries.filter { !it.directory }.map { Channel(it.name, it.ref, source.name) }, entries, parents)
                }
                else -> ResumeContents(emptyList())
            }
            loaded[key] = result; return result
        }
        val contents = resolve(saved.source, true)
        if (generation != resumeGeneration || !startupPending) return
        val restoredPlaying = saved.playing?.let { last ->
            contents.channels.firstOrNull { it.ref == last.ref }
                ?: saved.playingSource?.let { source ->
                    try { resolve(source, false).channels.firstOrNull { it.ref == last.ref } }
                    catch (e: CancellationException) { throw e } catch (_: Exception) { null }
                }
        }
        if (generation != resumeGeneration || !startupPending) return
        check(contents.channels.isNotEmpty() || contents.entries.isNotEmpty()) { "Liste mémorisée indisponible" }
        navigationKind = saved.source.kind
        folderPlayback = false; satelliteName = ""; satelliteRef = null
        when (saved.source.kind) {
            "all" -> { navigationKind = "bouquet"; bouquet = "" }
            "bouquet" -> bouquet = saved.source.name
            "satellite" -> { satelliteName = saved.source.name; satelliteRef = saved.source.ref; satelliteServices = contents.channels }
            "folder" -> {
                folderTitle = saved.source.name; folderRef = saved.source.ref; folderEntries = contents.entries
                folderHistory.clear(); contents.parents.forEach { folderHistory.addLast(it) }
                folderPlayback = contents.entries.none { it.directory }
                folderPlaybackTitle = folderTitle; folderChannels = contents.channels
                folderIndex = restoredIndex(contents.entries.map { it.ref }, saved.selectedRef, saved.index)
            }
        }
        val restoredCursor = restoredIndex(contents.channels.map { it.ref }, saved.selectedRef, saved.index)
        index = restoredCursor
        playingSource = saved.playingSource ?: saved.source
        if (restoredPlaying != null) play(restoredPlaying, restoring = true, force = true)
        index = restoredCursor
        page = if (saved.source.kind == "folder" && !folderPlayback) "folders" else if (saved.page == "player" && restoredPlaying != null) "player" else "channels"
        restoreSelectionOnNextList = page == "player"
        startupPending = false; resumeUnresolved = false; sessionReady = true
        Log.i("NeoResume", "restored kind=${saved.source.kind} index=$index count=${contents.channels.size} playback=${restoredPlaying != null}")
        if (saved.playing != null && restoredPlaying == null) playbackMessage = "Dernière chaîne absente de la liste reçue. Choisis une chaîne disponible."
    }
    fun startWeather() { scope.launch {
        while (isActive) {
            try { val loc = receiverApi.weatherLocation(); weather = Weather.fetch(loc.city, loc.latitude, loc.longitude) }
            catch (e: CancellationException) { throw e } catch (_: Exception) { /* Keep last observation, never invent temperatures. */ }
            delay(1800000)
        }
    } }
    fun openSatellites() {
        bouquetIndex = 0; page = "satellites"
        if (satellites.isEmpty()) scope.launch {
            try { satellites = receiverApi.satellites() }
            catch (e: CancellationException) { throw e } catch (e: Exception) { message("Satellites", "Liste indisponible : ${e.message}") }
        }
    }
    fun chooseSatellite(satellite: Satellite) {
        cancelStartupResume(); navigationKind = "satellite"; satelliteRef = satellite.ref
        satelliteJob?.cancel(); val generation = ++satelliteGeneration
        folderPlayback = false
        satelliteName = satellite.name; index = 0; page = "channels"
        val cached = satelliteCache[satellite.ref]
        satelliteServices = cached.orEmpty(); busy = cached == null
        if (cached != null) return
        val api = receiverApi
        satelliteJob = scope.launch {
            try {
                val services = api.satelliteChannels(satellite)
                if (generation == satelliteGeneration) { satelliteCache[satellite.ref] = services; satelliteServices = services }
            }
            catch (e: CancellationException) { throw e } catch (e: Exception) { if (generation == satelliteGeneration) message("Satellites", "Chaînes indisponibles : ${e.message}") }
            finally { if (generation == satelliteGeneration) busy = false }
        }
    }
    fun selectGroup() {
        if (page == "satellites") satellites.getOrNull(bouquetIndex)?.let { chooseSatellite(it) }
        else bouquets.getOrNull(bouquetIndex)?.let { chooseBouquet(it) }
    }
    fun browseFolder(ref: String?, title: String, root: Boolean = false) {
        cancelStartupResume(); navigationKind = "folder"
        folderPlayback = false
        folderJob?.cancel(); val generation = ++folderGeneration
        if (root) folderHistory.clear()
        else folderHistory.addLast(FolderFrame(folderTitle, folderRef, folderEntries, folderIndex))
        folderRef = ref; folderTitle = title; folderIndex = 0; page = "folders"
        val key = ref.orEmpty(); val cached = folderCache[key]
        folderEntries = cached.orEmpty(); folderBusy = cached == null
        if (cached != null) { showFolderEntries(cached); return }
        val api = receiverApi
        folderJob = scope.launch {
            try {
                val entries = api.entries(ref)
                if (generation == folderGeneration) {
                    folderCache[key] = entries; showFolderEntries(entries)
                    Log.i("NeoFolders", "loaded depth=${folderHistory.size} folders=${entries.count { it.directory }} channels=${entries.count { !it.directory }}")
                }
            } catch (e: CancellationException) { throw e }
            catch (e: Exception) { if (generation == folderGeneration) message("Bouquets", "Ouverture impossible : ${e.message}") }
            finally { if (generation == folderGeneration) folderBusy = false }
        }
    }
    private fun showFolderEntries(entries: List<ServiceEntry>) {
        folderEntries = entries
        folderPlayback = false
        if (entries.isNotEmpty() && entries.none { it.directory }) {
            folderChannels = entries.map { Channel(it.name, it.ref, folderTitle) }
            folderPlaybackTitle = folderTitle; folderPlayback = true; index = 0; page = "channels"
        }
    }
    fun activateFolder() {
        val entry = folderEntries.getOrNull(folderIndex) ?: return
        if (entry.directory) {
            if (entry.ref == folderRef || folderHistory.any { it.ref == entry.ref }) {
                message("Bouquets", "Ce dossier renvoie vers un niveau déjà ouvert."); return
            }
            browseFolder(entry.ref, entry.name)
        } else {
            folderChannels = folderEntries.filter { !it.directory }.map { Channel(it.name, it.ref, folderTitle) }
            folderPlaybackTitle = folderTitle; folderPlayback = true
            index = folderChannels.indexOfFirst { it.ref == entry.ref }.coerceAtLeast(0)
            play(Channel(entry.name, entry.ref, folderTitle))
        }
    }
    private fun folderBack() {
        folderJob?.cancel(); folderGeneration++; folderBusy = false
        val previous = folderHistory.pollLast()
        if (previous == null) { page = if (playing != null) "player" else "channels"; return }
        navigationKind = "folder"; folderPlayback = false
        folderTitle = previous.title; folderRef = previous.ref; folderEntries = previous.entries; folderIndex = previous.index; page = "folders"
        showFolderEntries(previous.entries)
    }
    suspend fun loadIcon(ch: Channel) {
        if (meta[ch.ref]?.icon != null || !loadingIcons.add(ch.ref)) return
        val config = settings; val api = receiverApi
        try { iconPermits.withPermit {
            val icon = picons.get(config, ch) { api.picon(ch) }
            if (settings == config && icon != null) {
                if (meta.size >= 100) meta.keys.firstOrNull { it != selected?.ref && it != playing?.ref }?.let { meta.remove(it) }
                val previous = meta[ch.ref]
                meta[ch.ref] = previous?.copy(icon = icon) ?: Meta(emptyList(), icon, 0)
            }
        } } catch (e: CancellationException) { throw e } catch (_: Exception) { /* A missing picon never hides the list. */ }
        finally { loadingIcons.remove(ch.ref) }
    }

    private fun createMediaFactory(config: ReceiverSettings, receiverAuth: Boolean = true): DefaultMediaSourceFactory {
        val headers = if (!receiverAuth || config.username.isBlank()) emptyMap() else mapOf("Authorization" to "Basic " +
            android.util.Base64.encodeToString((config.username + ":" + config.password).toByteArray(), android.util.Base64.NO_WRAP))
        val http = DefaultHttpDataSource.Factory().setConnectTimeoutMs(8000).setReadTimeoutMs(15000).setDefaultRequestProperties(headers)
        return DefaultMediaSourceFactory(context).setDataSourceFactory(DataSource.Factory {
            val source = http.createDataSource()
            if (receiverAuth) ReceiverStreamDataSource(source, config) else source
        }).setLoadErrorHandlingPolicy(object : DefaultLoadErrorHandlingPolicy() {
            override fun getRetryDelayMsFor(loadErrorInfo: LoadErrorHandlingPolicy.LoadErrorInfo): Long {
                if (generateSequence(loadErrorInfo.exception as Throwable?) { it.cause }.any { it is ReceiverStreamException }) return C.TIME_UNSET
                return super.getRetryDelayMsFor(loadErrorInfo)
            }
        })
    }
    private fun afterFirstFrame(sequence: Long) {
        afterFrameJob?.cancel()
        val ch = playing ?: return
        val api = receiverApi
        afterFrameJob = scope.launch {
            delay(400)
            if (sequence != zapSequence) return@launch
            launch { loadMeta(ch, priority = true) }; launch { loadIcon(ch) }
            // Resolve M3U addresses only. Do not open neighbouring video streams/tuners.
            val list = visible
            val at = list.indexOfFirst { it.ref == ch.ref }
            if (at >= 0) for (offset in listOf(1, -1)) {
                ensureActive()
                val next = list[Math.floorMod(at + offset, list.size)]
                try { api.stream(next) } catch (e: CancellationException) { throw e } catch (_: Exception) { /* optional warm-up */ }
            }
        }
    }

    fun connect(config: ReceiverSettings, restore: Boolean = false) {
        if (busy) return
        busy = true; status = "Connexion au Vu+ ${config.host}…"
        scope.launch {
            try {
                val generation = resumeGeneration
                val saved = if (restore && startupPending) withContext(Dispatchers.IO) { resumeStore.read(config) } else null
                if (saved != null && startupPending) resumeUnresolved = true
                val cached = if (channels.isEmpty() && config == settings) channelStore.read(config) else emptyList()
                val cacheShown = cached.isNotEmpty()
                if (cacheShown) {
                    channels = cached
                    if (bouquet.isNotBlank() && bouquet !in bouquets) bouquet = bouquets.firstOrNull().orEmpty()
                    if (saved != null && startupPending && saved.source.kind in setOf("all", "bouquet")) {
                        bouquet = if (saved.source.kind == "all") "" else saved.source.name
                        index = restoredIndex(visible.map { it.ref }, saved.selectedRef, saved.index)
                    }
                    status = "Liste en cache • actualisation OpenWebif…"
                    Log.i("NeoLists", "cached_list services=${cached.size}")
                }
                val api = OpenWebif(config)
                var resumed = false
                // Validate the live receiver and install its HTTP/auth factory before autoplay.
                api.ping(); val list = api.channels()
                check(list.isNotEmpty()) { "Aucune chaîne reçue" }
                val changedReceiver = config.host != settings.host || config.port != settings.port || config.username != settings.username
                val selectedRef = selected?.ref; val oldIndex = index
                settings = config; receiverApi = api; mediaFactory = createMediaFactory(config)
                folderCache.clear()
                satelliteCache.clear()
                channels = list
                if (changedReceiver) {
                    resumeStore.nextGeneration()
                    player.stop(); gstInstance?.stop(); playing = null; playingSource = null; previous = null; previousSource = null
                    navigationKind = "bouquet"; folderPlayback = false; satelliteName = ""; index = 0
                } else if (navigationKind == "bouquet") index = restoredIndex(visible.map { it.ref }, selectedRef, oldIndex)
                if (!cacheShown && !resumed) meta.clear()
                if (bouquet.isNotBlank() && bouquet !in bouquets) bouquet = bouquets.firstOrNull().orEmpty()
                if (!resumed && saved != null && startupPending) {
                    try { restoreResume(saved, api, generation); resumed = !startupPending }
                    catch (e: CancellationException) { throw e } catch (_: Exception) { Log.i("NeoResume", "source_unavailable") }
                }
                credentials.save(config)
                prefs.edit().putString("bouquet", bouquet).apply()
                status = "${list.size} services • ${bouquets.size} bouquets"; if (!cacheShown && !resumed && startupPending) page = "channels"
                channelStore.write(config, list)
            } catch (e: CancellationException) { throw e }
            catch (e: Exception) { status = "Vu+ inaccessible : ${e.message}" }
            finally { busy = false; startupPending = false; sessionReady = !resumeUnresolved }
        }
    }
    suspend fun loadMeta(ch: Channel, priority: Boolean = false) {
        if (meta[ch.ref]?.let { System.currentTimeMillis() - it.fetched < 120000 } == true) return
        val config = settings
        (if (priority) selectedMetaPermit else permits).withPermit {
            if (meta[ch.ref]?.let { System.currentTimeMillis() - it.fetched < 120000 } == true) return@withPermit
            if (!loadingMeta.add(ch.ref)) return@withPermit
            try {
            val api = receiverApi
            val events = try { api.programmes(ch) } catch (e: CancellationException) { throw e } catch (_: Exception) { emptyList() }
            if (settings == config) {
                if (meta.size >= 100) meta.keys.firstOrNull { it != playing?.ref && it != selected?.ref }?.let { meta.remove(it) }
                meta[ch.ref] = Meta(events, meta[ch.ref]?.icon, System.currentTimeMillis())
            }
            } finally { loadingMeta.remove(ch.ref) }
        }
    }
    fun chooseBouquet(name: String) { cancelStartupResume(); navigationKind = "bouquet"; folderPlayback = false; satelliteName = ""; bouquet = name; index = 0; page = "channels"; prefs.edit().putString("bouquet", name).apply() }
    fun showBanner() { banner = true; bannerJob?.cancel(); bannerJob = scope.launch { delay(6000); banner = false } }
    fun play(ch: Channel, restoring: Boolean = false, force: Boolean = false) {
        if (!restoring) cancelStartupResume()
        if (isDirectoryRef(ch.ref)) { browseFolder(ch.ref, ch.name, root = true); return }
        if (!restoring) {
            val source = when {
                visible.any { it.ref == ch.ref } -> currentSource()
                previous?.ref == ch.ref && previousSource != null -> previousSource!!
                else -> ResumeSource("all")
            }
            if (playing?.ref != ch.ref) previousSource = playingSource
            playingSource = source
        }
        if (!force && playing?.ref == ch.ref && playbackReady) {
            page = "player"; resumePlayback(); showBanner(); return
        }
        val coalesce = (if (engine != "Media3") playing != null && !gstReady else player.playbackState == Player.STATE_BUFFERING) || tuneJob?.isActive == true
        zapSequence++; zapStartedAt = SystemClock.elapsedRealtime()
        val sequence = zapSequence
        playbackFailed = false
        if (force) receiverApi.invalidateStream(ch)
        gstReady = false; gstVideo = null; gstAudioTracks = 0; gstTextTracks = 0; gstAudioSelected = 0; gstTextSelected = -1
        Log.i("NeoZap", "request id=$sequence")
        tuneJob?.cancel(); afterFrameJob?.cancel(); playbackMonitor?.cancel(); if (playing?.ref != ch.ref) previous = playing
        visible.indexOfFirst { it.ref == ch.ref }.takeIf { it >= 0 }?.let { index = it }
        playing = ch; page = "player"; playbackMessage = "Ouverture du flux…"; showBanner()
        // Playback control must not wait for Compose's next UI frame.
        tuneJob = scope.launch(Dispatchers.Main.immediate) {
            try {
                // Only coalesce repeats during an unfinished tune, never a normal zap.
                if (coalesce) delay(120)
                val cached = receiverApi.cachedStream(ch)
                val url = cached ?: receiverApi.stream(ch)
                ensureActive()
                Log.i("NeoZap", "resolved id=$sequence cached=${cached != null} elapsed_ms=${SystemClock.elapsedRealtime() - zapStartedAt}")
                val receiverAuth = usesReceiverAuthentication(url, settings)
                if (engine == "GStreamer") {
                    player.stop()
                    gstPlayer().open(url, if (receiverAuth) settings.username else "", if (receiverAuth) settings.password else "", sequence)
                } else {
                    val factory = if (receiverAuth) mediaFactory else internetMediaFactory
                    player.setMediaSource(factory.createMediaSource(MediaItem.Builder().setUri(url).setMediaId(sequence.toString()).build()))
                    player.prepare(); player.playWhenReady = true
                    monitorPlayback(sequence)
                }
            } catch (e: CancellationException) { throw e } catch (e: Exception) {
                playbackFailed = true; playbackMessage = "Flux indisponible. OK : réessayer."; banner = true
                Log.i("NeoZap", "resolve_error id=$sequence type=${e.javaClass.simpleName}")
            }
        }
    }
    fun move(delta: Int) { if (visible.isNotEmpty()) index = Math.floorMod(index + delta, visible.size) }
    private fun pageMove(direction: Int) {
        when (page) {
            "folders" -> folderIndex = (folderIndex + 20 * direction).coerceIn(0, folderEntries.lastIndex.coerceAtLeast(0))
            "bouquets", "satellites" -> bouquetIndex = (bouquetIndex + 20 * direction).coerceIn(0, ((if (page == "satellites") satellites.size else bouquets.size) - 1).coerceAtLeast(0))
            "tracks" -> detailIndex = (detailIndex + 10 * direction).coerceIn(0, tracks().lastIndex.coerceAtLeast(0))
            "menu" -> menuIndex = Math.floorMod(menuIndex + direction, 5)
            else -> if (visible.isNotEmpty()) index = (index + 20 * direction).coerceIn(0, visible.lastIndex)
        }
    }
    private fun monitorPlayback(sequence: Long) {
        playbackMonitor = scope.launch {
            while (isActive && sequence == zapSequence && engine == "Media3") {
                delay(10000)
                if (sequence != zapSequence || engine != "Media3") break
                val counters = player.videoDecoderCounters
                counters?.ensureUpdated()
                Log.i("NeoPlayback", "id=$sequence state=${player.playbackState} playing=${player.isPlaying} position_ms=${player.currentPosition} buffered_ms=${player.totalBufferedDuration} rendered=${counters?.renderedOutputBufferCount ?: -1} dropped=${counters?.droppedBufferCount ?: -1}")
            }
        }
    }
    fun zap(delta: Int) {
        if (visible.isEmpty()) return
        index = Math.floorMod(visible.indexOfFirst { it.ref == playing?.ref }.coerceAtLeast(0) + delta, visible.size)
        play(visible[index])
    }
    fun back() {
        if (messageTitle.isNotBlank()) { messageTitle = ""; return }
        if (number.isNotBlank()) { numberJob?.cancel(); number = ""; return }
        if (page == "folders") { folderBack(); return }
        if (folderPlayback && page == "channels") {
            if (folderEntries.any { it.directory }) page = "folders" else folderBack()
            return
        }
        page = when (page) {
            "player" -> if (banner) { banner = false; "player" } else "channels"
            "channels", "menu" -> if (playing != null) "player" else if (page == "channels") "menu" else "channels"
            "event", "tracks" -> if (playing != null) "player" else "channels"
            "information" -> "menu"
            else -> "channels"
        }
    }
    fun message(title: String, body: String) { messageTitle = title; messageBody = body }
    fun openBouquets() { browseFolder(null, "Bouquets TV", root = true) }
    fun openGuide() { detailIndex = 0; page = "guide" }
    fun activateMenu() {
        when (menuIndex) {
            0 -> message("Plugin Browser", "Les plugins Enigma2 s’exécutent sur le Vu+. Leur installation et leur interface native ne sont pas portées dans cette application Android.")
            1 -> page = "settings"
            2 -> { page = "information"; information = "Chargement des programmations…"; scope.launch {
                information = try { OpenWebif(settings).timers().joinToString("\n\n").ifBlank { "Aucune programmation sur le Vu+." } }
                catch (e: CancellationException) { throw e } catch (e: Exception) { "Programmations indisponibles : ${e.message}" }
            } }
            3 -> message("Veille / Redémarrage", "La touche POWER de la télécommande Sony gère la veille de la TV. La veille et le redémarrage du Vu+ ne sont pas commandés par cette application.")
            4 -> { page = "information"; information = "Metrix NEO TV $appVersion\n\n$status\nVu+ : ${settings.host}:${settings.port}\n\nSkin : MetrixNEO du dépôt, liste compacte 20 lignes.\nInterface Android native ; plugins et réglages système Enigma2 non portés.\n\nMENU : menu principal   •   GUIDE : EPG   •   CH +/− : zapper\nOK : infobar / valider   •   ↑↓ en TV : liste des chaînes\n←→ en TV : chaîne précédente / suivante\nBleu : bouquets   •   Rouge : tous les services\n0 : chaîne précédente   •   1–9 : numéro de chaîne" }
        }
    }
    private fun confirmNumber() {
        val at = (number.toIntOrNull() ?: 0) - 1; number = ""
        if (page == "folders") {
            if (at in folderEntries.indices) { folderIndex = at; activateFolder() }
            else message("Bouquets", "Ce numéro n’existe pas dans le dossier courant.")
            return
        }
        if (page in listOf("satellites", "bouquets")) {
            val count = if (page == "satellites") satellites.size else bouquets.size
            if (at in 0 until count) { bouquetIndex = at; selectGroup() }
            else message("Numéro", "Ce numéro n’existe pas dans cette liste.")
            return
        }
        if (page == "menu") {
            if (at in 0..4) { menuIndex = at; activateMenu() }
            return
        }
        if (page == "tracks") { if (at in tracks().indices) selectTrack(at); return }
        visible.getOrNull(at)?.let { index = at; play(it) } ?: message("Numéro de chaîne", "Ce numéro n’existe pas dans le bouquet courant.")
    }
    private fun digit(value: Int) {
        if (value == 0 && number.isEmpty() && playing != null) { previous?.let { play(it) }; return }
        if (number.length >= 6) number = ""
        number += value.toString(); numberJob?.cancel(); numberJob = scope.launch { delay(1400); confirmNumber() }
    }
    fun tracks(): List<Triple<Int, Int, String>> = buildList {
        if (engine == "GStreamer") {
            repeat(gstAudioTracks) { add(Triple(1, it, "Audio ${it + 1}" + if (gstAudioSelected == it) "  ✓" else "")) }
            repeat(gstTextTracks) { add(Triple(3, it, "Sous-titres ${it + 1}" + if (gstTextSelected == it) "  ✓" else "")) }
            add(Triple(3, -1, "Désactiver les sous-titres"))
            return@buildList
        }
        player.currentTracks.groups.forEachIndexed { gi, group ->
            if (group.type == C.TRACK_TYPE_AUDIO || group.type == C.TRACK_TYPE_TEXT) for (ti in 0 until group.length) if (group.isTrackSupported(ti)) {
                val f = group.getTrackFormat(ti)
                add(Triple(gi, ti, (if (group.type == C.TRACK_TYPE_AUDIO) "Audio" else "Sous-titres") + " • " + listOfNotNull(f.language, f.label, f.sampleMimeType).distinct().joinToString(" • ") + if (group.isTrackSelected(ti)) "  ✓" else ""))
            }
        }
        add(Triple(-1, -1, "Désactiver les sous-titres"))
    }
    fun selectTrack(at: Int) {
        if (engine == "GStreamer") {
            tracks().getOrNull(at)?.let {
                gstInstance?.selectTrack(it.first, it.second)
                if (it.first == 1) gstAudioSelected = it.second else gstTextSelected = it.second
            }
            page = "player"; showBanner(); return
        }
        val track = tracks().getOrNull(at) ?: return; val b = player.trackSelectionParameters.buildUpon()
        if (track.first < 0) b.setTrackTypeDisabled(C.TRACK_TYPE_TEXT, true)
        else { val group = player.currentTracks.groups[track.first]; b.setTrackTypeDisabled(group.type, false).setOverrideForType(TrackSelectionOverride(group.mediaTrackGroup, track.second)) }
        player.trackSelectionParameters = b.build(); page = "player"; showBanner()
    }
    fun key(e: KeyEvent): Boolean {
        val k = e.keyCode
        if (e.action == ACTION_DOWN && e.repeatCount == 0) cancelStartupResume()
        // Consume both edges so a hardware press cannot also invoke platform BackHandler.
        if (k == KEYCODE_BACK || k == KEYCODE_ESCAPE) {
            if (e.action == ACTION_DOWN && e.repeatCount == 0) onExit()
            return true
        }
        if (e.action == ACTION_DOWN) onInteraction()
        if (page == "settings" && k !in listOf(KEYCODE_BACK, KEYCODE_ESCAPE, KEYCODE_MENU, KEYCODE_TV_CONTENTS_MENU, KEYCODE_TV_MEDIA_CONTEXT_MENU)) return false
        val supported = k in KEYCODE_0..KEYCODE_9 || k in listOf(KEYCODE_MENU, KEYCODE_TV_CONTENTS_MENU, KEYCODE_TV_MEDIA_CONTEXT_MENU, KEYCODE_INFO, KEYCODE_GUIDE,
            KEYCODE_DPAD_UP, KEYCODE_DPAD_DOWN, KEYCODE_DPAD_LEFT, KEYCODE_DPAD_RIGHT, KEYCODE_DPAD_CENTER, KEYCODE_ENTER, KEYCODE_NUMPAD_ENTER,
            KEYCODE_CHANNEL_UP, KEYCODE_CHANNEL_DOWN, KEYCODE_PAGE_UP, KEYCODE_PAGE_DOWN, KEYCODE_PROG_RED, KEYCODE_PROG_GREEN, KEYCODE_PROG_YELLOW, KEYCODE_PROG_BLUE,
            KEYCODE_MEDIA_PLAY_PAUSE, KEYCODE_MEDIA_PLAY, KEYCODE_MEDIA_PAUSE, KEYCODE_CAPTIONS, KEYCODE_MEDIA_AUDIO_TRACK)
        if (!supported) return false
        if (e.action != ACTION_DOWN) return true
        if (e.repeatCount > 0 && k !in listOf(KEYCODE_DPAD_UP, KEYCODE_DPAD_DOWN, KEYCODE_DPAD_LEFT, KEYCODE_DPAD_RIGHT,
                KEYCODE_CHANNEL_UP, KEYCODE_CHANNEL_DOWN, KEYCODE_PAGE_UP, KEYCODE_PAGE_DOWN)) return true
        if (messageTitle.isNotBlank()) { if (k in listOf(KEYCODE_BACK, KEYCODE_ESCAPE, KEYCODE_DPAD_CENTER, KEYCODE_ENTER)) messageTitle = ""; return true }
        if (k in KEYCODE_0..KEYCODE_9) { if (e.repeatCount == 0) digit(k - KEYCODE_0); return true }
        when (k) {
            KEYCODE_MENU, KEYCODE_TV_CONTENTS_MENU, KEYCODE_TV_MEDIA_CONTEXT_MENU -> if (page == "menu") back() else { page = "menu" }
            KEYCODE_GUIDE -> openGuide()
            KEYCODE_INFO -> if (page == "player") { page = "event" } else openGuide()
            KEYCODE_PROG_BLUE -> openBouquets()
            KEYCODE_PROG_RED -> if (page == "menu") back() else chooseBouquet("")
            KEYCODE_PROG_GREEN -> openSatellites()
            KEYCODE_PROG_YELLOW -> if (page == "channels") toggleListVideo() else message("Réception / fournisseurs", "Vert : liste des satellites. Bleu : bouquets et sous-dossiers. Le classement par fournisseur n’est pas encore porté.")
            KEYCODE_CHANNEL_UP, KEYCODE_CHANNEL_DOWN -> {
                if (page == "player") zap(if (k == KEYCODE_CHANNEL_UP) 1 else -1)
                else pageMove(if (k == KEYCODE_CHANNEL_UP) -1 else 1)
            }
            KEYCODE_MEDIA_PLAY_PAUSE -> if (isPlaybackPlaying) pausePlayback() else resumePlayback()
            KEYCODE_MEDIA_PLAY -> resumePlayback()
            KEYCODE_MEDIA_PAUSE -> pausePlayback()
            KEYCODE_CAPTIONS, KEYCODE_MEDIA_AUDIO_TRACK -> if (playing != null) { page = "tracks"; detailIndex = 0 }
            KEYCODE_DPAD_UP, KEYCODE_DPAD_DOWN -> {
                val d = if (k == KEYCODE_DPAD_UP) -1 else 1
                when (page) {
                    "folders" -> folderIndex = Math.floorMod(folderIndex + d, folderEntries.size.coerceAtLeast(1))
                    "player" -> { page = "channels"; if (!restoreSelectionOnNextList) index = visible.indexOfFirst { it.ref == playing?.ref }.coerceAtLeast(0); restoreSelectionOnNextList = false }
                    "bouquets", "satellites" -> bouquetIndex = Math.floorMod(bouquetIndex + d, (if (page == "satellites") satellites.size else bouquets.size).coerceAtLeast(1))
                    "guide" -> detailIndex = (detailIndex + d).coerceIn(0, ((selected?.let { meta[it.ref]?.events?.size } ?: 1) - 1).coerceAtLeast(0))
                    "tracks" -> detailIndex = (detailIndex + d).coerceIn(0, tracks().lastIndex.coerceAtLeast(0))
                    "menu" -> menuIndex = Math.floorMod(menuIndex + d, 5)
                    else -> move(d)
                }
            }
            KEYCODE_DPAD_LEFT, KEYCODE_DPAD_RIGHT, KEYCODE_PAGE_UP, KEYCODE_PAGE_DOWN -> {
                val d = if (k == KEYCODE_DPAD_LEFT || k == KEYCODE_PAGE_UP) -1 else 1
                when (page) {
                    "player" -> zap(d)
                    "menu" -> menuIndex = Math.floorMod(menuIndex + d, 5)
                    "guide" -> { move(d); detailIndex = 0 }
                    else -> pageMove(d)
                }
            }
            KEYCODE_DPAD_CENTER, KEYCODE_ENTER, KEYCODE_NUMPAD_ENTER -> {
                if (number.isNotBlank()) { numberJob?.cancel(); confirmNumber(); return true }
                when (page) {
                    "folders" -> activateFolder()
                    "menu" -> activateMenu()
                    "bouquets", "satellites" -> selectGroup()
                    "player" -> if (playbackFailed) playing?.let { play(it, force = true) } else if (banner) banner = false else showBanner()
                    "event" -> page = "player"
                    "tracks" -> selectTrack(detailIndex)
                    "information" -> page = "menu"
                    else -> selected?.let { play(it) } ?: run { page = "settings" }
                }
            }
        }
        return true
    }
}

@Composable private fun TextLine(value: String, size: Int = 24, color: Color = Neo.white, modifier: Modifier = Modifier, lines: Int = Int.MAX_VALUE, bold: Boolean = false) {
    Text(value, modifier, color, fontSize = size.sp, lineHeight = (size * 1.17f).sp, fontWeight = if (bold) FontWeight.Bold else FontWeight.Normal, maxLines = lines, overflow = TextOverflow.Ellipsis)
}

/** Only the selected overflowing row animates; the text is never replaced with ellipses. */
private fun Modifier.selectedMarquee(active: Boolean): Modifier = basicMarquee(
    iterations = if (active) Int.MAX_VALUE else 0,
    initialDelayMillis = 1400,
    repeatDelayMillis = 1400,
    spacing = MarqueeSpacing(48.dp),
    velocity = 48.dp
)
@Composable private fun Asset(id: Int, modifier: Modifier = Modifier) { Image(painterResource(id), null, modifier, contentScale = ContentScale.FillBounds) }

@Composable private fun Picon(m: Meta?, modifier: Modifier) {
    val bitmap = m?.icon
    val image = remember(bitmap) { bitmap?.asImageBitmap() }
    if (image != null) Image(image, null, modifier, contentScale = ContentScale.Fit)
    else Box(modifier, contentAlignment = Alignment.Center) { Asset(R.drawable.menu_television, Modifier.size(34.dp)) }
}
@Composable private fun Progress(value: Float, modifier: Modifier) {
    Box(modifier.height(11.dp).background(Neo.track)) { if (value > 0) Box(Modifier.fillMaxHeight().fillMaxWidth(value.coerceIn(0f, 1f)).background(Neo.cyan)) }
}
private fun time(seconds: Long) = if (seconds <= 0) "--:--" else SimpleDateFormat("HH:mm", Locale.FRANCE).format(Date(seconds * 1000))
@Composable private fun Header(title: String) {
    Row(Modifier.fillMaxWidth().height(108.dp).padding(horizontal = 48.dp), verticalAlignment = Alignment.CenterVertically) {
        Asset(R.drawable.menu_television, Modifier.size(48.dp)); Spacer(Modifier.width(30.dp))
        Text(title, Modifier.weight(1f).selectedMarquee(true), color = Neo.white, fontSize = 43.sp,
            lineHeight = 50.sp, maxLines = 1, softWrap = false, overflow = TextOverflow.Clip)
        WeatherClock(Modifier.width(1000.dp).height(92.dp))
    }
}
@Composable private fun WeatherClock(modifier: Modifier = Modifier) {
    val weather = LocalWeather.current
    var now by remember { mutableLongStateOf(System.currentTimeMillis()) }
    LaunchedEffect(Unit) { while (true) { now = System.currentTimeMillis(); delay(60_000L - now % 60_000L) } }
    Row(modifier.background(Neo.panel).border(1.dp, Neo.line, RoundedCornerShape(10.dp)).padding(horizontal = 14.dp, vertical = 5.dp), verticalAlignment = Alignment.CenterVertically) {
        Column(Modifier.width(205.dp)) {
            TextLine(weather?.city ?: "Météo du Vu+", 22, lines = 1)
            TextLine(weather?.let { "${Weather.icon(it.code, it.isDay)}  ${it.temperature}°C" } ?: "En attente…", 32, Neo.white, lines = 1)
            TextLine("Open-Meteo · CC BY 4.0", 12, Neo.muted, lines = 1)
        }
        weather?.days?.forEach { day ->
            Column(Modifier.width(125.dp).border(1.dp, Neo.line), horizontalAlignment = Alignment.CenterHorizontally) {
                TextLine(java.time.LocalDate.parse(day.date).dayOfWeek.getDisplayName(java.time.format.TextStyle.SHORT, Locale.FRANCE), 19)
                TextLine(Weather.icon(day.code), 28, Neo.cyan)
                TextLine("${day.max}°/${day.min}°", 19)
            }
        }
        Spacer(Modifier.weight(1f))
        Column(Modifier.width(215.dp), horizontalAlignment = Alignment.End) {
            TextLine(SimpleDateFormat("EEEE", Locale.FRANCE).format(Date(now)), 20, Neo.muted)
            TextLine(SimpleDateFormat("dd MMMM yyyy", Locale.FRANCE).format(Date(now)), 20, Neo.muted)
        }
        TextLine(SimpleDateFormat("HH:mm", Locale.FRANCE).format(Date(now)), 44, modifier = Modifier.padding(start = 20.dp), lines = 1)
    }
}
@Composable private fun Footer(labels: List<String>, actions: List<() -> Unit>, modifier: Modifier = Modifier) {
    Row(modifier.fillMaxWidth().height(64.dp), verticalAlignment = Alignment.CenterVertically) {
        labels.forEachIndexed { i, label -> Row(Modifier.weight(1f).clickable { actions.getOrNull(i)?.invoke() }, verticalAlignment = Alignment.CenterVertically) {
            Box(Modifier.width(8.dp).height(44.dp).background(Neo.colors[i])); TextLine(label, 23, modifier = Modifier.padding(start = 16.dp), lines = 2)
        } }
        TextLine("INFO • MENU • EXIT", 21, Neo.muted)
    }
}

@androidx.annotation.OptIn(androidx.media3.common.util.UnstableApi::class)
@Composable private fun Screen(s: ReceiverUi) {
    BackgroundEffects(s)
    val focus = remember { FocusRequester() }
    LaunchedEffect(s.page) { if (s.page != "settings") focus.requestFocus() }
    BoxWithConstraints(Modifier.fillMaxSize().semantics { testTagsAsResourceId = true }.background(Neo.bg).onPreviewKeyEvent { s.key(it.nativeKeyEvent) }.focusRequester(focus).focusable()) {
        // All geometry/text scales from the skin's native 1920×1080 coordinate space.
        val scale = LocalDensity.current.density * maxWidth.value / 1920f
        CompositionLocalProvider(LocalDensity provides Density(scale, 1f), LocalWeather provides s.weather) {
            Box(Modifier.fillMaxSize()) {
                if (s.playing != null) key(s.engine) {
                    // Keep one live surface/decoder while moving between list and full screen.
                    val video = if (s.page == "channels" && s.listMiniTv)
                        Modifier.align(Alignment.TopEnd).padding(top = 108.dp, end = 24.dp).size(640.dp, 360.dp)
                    else Modifier.fillMaxSize()
                    Box(video.testTag("neo.videoSurface")) {
                        if (s.engine == "GStreamer") AndroidView(factory = { s.gstPlayer().view() }, modifier = Modifier.fillMaxSize())
                        else AndroidView(factory = { PlayerView(it).apply { setEnableComposeSurfaceSyncWorkaround(true); player = s.player; useController = false; isFocusable = false; setShowBuffering(PlayerView.SHOW_BUFFERING_WHEN_PLAYING) } }, update = { it.player = s.player }, modifier = Modifier.fillMaxSize())
                    }
                }
                when (s.page) {
                    "folders" -> Folders(s)
                    "player" -> Box(Modifier.fillMaxSize().testTag("neo.player")) { if (s.banner) Infobar(s); if (s.playbackMessage.isNotBlank()) Box(Modifier.align(Alignment.Center).background(Neo.panel).padding(28.dp)) { TextLine(s.playbackMessage, 28) } }
                    "channels" -> Channels(s)
                    "menu" -> MainMenu(s)
                    "bouquets", "satellites" -> Bouquets(s)
                    "guide" -> Guide(s)
                    "settings" -> Settings(s)
                    "tracks" -> Tracks(s)
                    "event" -> { val p = s.playing?.let { s.meta[it.ref]?.events?.firstOrNull() }; DetailPage(s.playing?.name.orEmpty(), (p?.title ?: "EPG indisponible") + "\n\n" + p?.description.orEmpty()) }
                    else -> DetailPage(if (s.menuIndex == 2) "Timers - Programmations" else "Information", s.information)
                }
                if (s.number.isNotBlank()) Box(Modifier.align(Alignment.TopEnd).padding(60.dp).background(Neo.panel).border(2.dp, Neo.cyan).padding(24.dp)) { TextLine(s.number, 64, Neo.cyan) }
                if (s.messageTitle.isNotBlank()) Box(Modifier.fillMaxSize().background(Color.Black.copy(alpha = .7f)), contentAlignment = Alignment.Center) {
                    Column(Modifier.width(1080.dp).background(Neo.panel).border(2.dp, Neo.cyan).padding(48.dp)) {
                        TextLine(s.messageTitle, 42); Spacer(Modifier.height(28.dp)); TextLine(s.messageBody, 30, Neo.muted); Spacer(Modifier.height(36.dp)); TextLine("OK / EXIT : fermer", 24, Neo.cyan)
                    }
                }
            }
        }
    }
    val rows = remember(s.visible, s.pageStart) { pageWindow(s.visible, s.pageStart) }
    LaunchedEffect(s.settings, rows, s.page) { if (s.page in listOf("channels", "guide")) { delay(150); coroutineScope { rows.sortedBy { it.ref != s.selected?.ref }.forEach { launch { s.loadIcon(it) }; launch { s.loadMeta(it) } } } } }
    val selected = if (s.page in listOf("channels", "guide")) s.selected else null
    LaunchedEffect(s.settings, selected, s.page) { selected?.let { delay(180); s.loadMeta(it, priority = true) } }

}

/** Observe resume saves without making every screen a reader of every cursor move. */
@OptIn(kotlinx.coroutines.FlowPreview::class)
@Composable private fun BackgroundEffects(s: ReceiverUi) {
    LaunchedEffect(s) {
        snapshotFlow { s.settings to s.resumeSnapshot() }.debounce(500).collectLatest { (receiver, resume) ->
            if (resume != null) s.persistResume(resume, receiver)
        }
    }
}

@Composable private fun Folders(s: ReceiverUi) {
    val start by remember(s) { derivedStateOf { s.folderIndex / 20 * 20 } }
    val rows = remember(s.folderEntries, start) { pageWindow(s.folderEntries, start) }
    Column(Modifier.fillMaxSize().testTag("neo.folders").background(Neo.bg)) {
        Header(s.folderTitle)
        Column(Modifier.weight(1f).padding(horizontal = 48.dp).border(1.dp, Neo.line)) {
            if (rows.isEmpty()) TextLine(if (s.folderBusy) "Chargement du dossier…" else "Dossier vide — RETOUR pour revenir", 30, Neo.muted, Modifier.padding(32.dp))
            rows.forEachIndexed { offset, entry ->
                key(entry.ref, start + offset) { FolderEntryRow(s, entry, start + offset, Modifier.weight(1f)) }
            }
            repeat((20 - rows.size).coerceAtLeast(0)) { Spacer(Modifier.weight(1f)) }
        }
        Footer(listOf("Tous les services", "Satellites", "RETOUR : dossier parent", "Bouquets TV"),
            listOf({ s.chooseBouquet("") }, { s.openSatellites() }, { s.back() }, { s.openBouquets() }), Modifier.padding(horizontal = 48.dp))
    }
}

@Composable private fun FolderEntryRow(s: ReceiverUi, entry: ServiceEntry, at: Int, modifier: Modifier) {
    Box(modifier.fillMaxWidth().testTag("neo.folder.$at").semantics { selected = s.folderIndex == at }.clickable { s.folderIndex = at; s.activateFolder() }) {
        Asset(R.drawable.selection_row, Modifier.matchParentSize().graphicsLayer { alpha = if (s.folderIndex == at) 1f else 0f })
        Row(Modifier.fillMaxSize().padding(horizontal = 24.dp), verticalAlignment = Alignment.CenterVertically) {
            TextLine(if (entry.directory) "▸" else "▶", 28, Neo.cyan, Modifier.width(55.dp))
            TextLine(entry.name, 27, modifier = Modifier.weight(1f), lines = 1)
            TextLine(if (entry.directory) "Dossier   •   OK : ouvrir" else "Chaîne   •   OK : regarder", 22, Neo.muted)
        }
    }
}

@Composable private fun Channels(s: ReceiverUi) {
    val list = s.visible; val selected = s.selected; val m = selected?.let { s.meta[it.ref] }
    val mini = s.listMiniTv
    Column(Modifier.fillMaxSize().testTag("neo.channels").semantics { stateDescription = if (mini) "mini-tv" else "transparent" }
        .background(if (mini) Color.Transparent else Neo.bg.copy(alpha = .48f))) {
        Header("TV - " + s.listTitle)
        Row(Modifier.weight(1f).padding(horizontal = 24.dp), horizontalArrangement = Arrangement.spacedBy(18.dp)) {
            Box(Modifier.weight(1218f).fillMaxHeight().background(Neo.panel.copy(alpha = if (mini) .94f else .40f)).border(1.dp, Neo.line)) {
                if (list.isEmpty()) Column(Modifier.padding(40.dp)) {
                    TextLine(if (s.busy) "Chargement des chaînes…" else "Aucune chaîne chargée", 34); Spacer(Modifier.height(24.dp)); TextLine(s.status, 26, Neo.muted)
                    Spacer(Modifier.height(32.dp)); TextLine("OK : configurer la connexion Vu+", 28, Neo.cyan, Modifier.clickable { s.page = "settings" })
                } else Column {
                    val rows = remember(list, s.pageStart) { pageWindow(list, s.pageStart) }
                    rows.forEachIndexed { offset, ch ->
                        val at = s.pageStart + offset; val active = at == s.index; val meta = s.meta[ch.ref]
                        ChannelRow(ch, meta, at, active, Modifier.weight(1f)) { s.index = at; s.play(ch) }
                    }
                    repeat(20 - rows.size) { Spacer(Modifier.weight(1f)) }
                }
            }
            Column(Modifier.weight(642f).fillMaxHeight()) {
              if (mini) {
                Box(Modifier.fillMaxWidth().height(360.dp).testTag("neo.miniTv").border(2.dp, Neo.cyan)) {
                    if (s.playing == null) Box(Modifier.fillMaxSize().background(Color.Black), contentAlignment = Alignment.Center) {
                        TextLine("Mini TV\nOK : lancer une chaîne", 28, Neo.muted, lines = 2)
                    }
                    if (s.playing != null && s.playbackMessage.isNotBlank()) Box(Modifier.align(Alignment.Center).background(Neo.panel.copy(alpha = .85f)).padding(12.dp)) {
                        TextLine(s.playbackMessage, 23, lines = 3)
                    }
                    TextLine(s.playing?.let { "Chaîne en cours : ${it.name}" } ?: "Aucune chaîne en lecture", 22,
                        modifier = Modifier.align(Alignment.BottomStart).fillMaxWidth().background(Neo.panel.copy(alpha = .80f)).padding(horizontal = 12.dp, vertical = 5.dp).testTag("neo.playingPreviewName"), lines = 1)
                }
                Spacer(Modifier.height(14.dp))
              }
              Column(Modifier.weight(1f).fillMaxWidth().background(Neo.panel.copy(alpha = if (mini) .94f else .78f))
                  .border(2.dp, Neo.line, RoundedCornerShape(8.dp)).padding(if (mini) 20.dp else 26.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) { Picon(m, Modifier.width(if (mini) 96.dp else 150.dp).height(if (mini) 54.dp else 94.dp)); Spacer(Modifier.width(24.dp)); TextLine(selected?.name ?: "Metrix NEO", if (mini) 29 else 34, modifier = Modifier.weight(1f).testTag("neo.selectedChannelName")) }
                Spacer(Modifier.height(if (mini) 12.dp else 30.dp)); TextLine(m?.events?.firstOrNull()?.title ?: "EPG indisponible", if (mini) 29 else 35, lines = if (mini) 3 else Int.MAX_VALUE)
                Spacer(Modifier.height(if (mini) 10.dp else 16.dp)); Progress(m?.events?.firstOrNull()?.progress() ?: 0f, Modifier.fillMaxWidth()); Spacer(Modifier.height(if (mini) 12.dp else 22.dp))
                TextLine(m?.events?.firstOrNull()?.description?.ifBlank { "Aucune description fournie par OpenWebif." } ?: "Programmes et picons chargés depuis le Vu+. Aucune donnée de démonstration.", if (mini) 22 else 25, Neo.muted, Modifier.weight(1f), if (mini) 6 else 15)
                m?.events?.drop(1)?.take(if (mini) 1 else 2)?.forEachIndexed { i, p -> TextLine("Suivant ${i + 1} :  ${time(p.begin)}  ${p.title}", 22, Neo.epg, lines = 2); Spacer(Modifier.height(if (mini) 6.dp else 12.dp)) }
                Box(Modifier.fillMaxWidth().height(1.dp).background(Neo.line)); Spacer(Modifier.height(20.dp)); TextLine("${if (list.isEmpty()) 0 else s.index + 1} / ${list.size}  •  ${s.listTitle}", 23, Neo.muted, lines = 2)
                TextLine("OK : regarder   •   ← → : page", 22, Neo.muted)
              }
            }
        }
        Footer(listOf("Tous les services", "Satellites", if (mini) "TV en fond / transparence" else "Mini TV", "Bouquets"), listOf({ s.chooseBouquet("") }, { s.openSatellites() }, { s.toggleListVideo() }, { s.openBouquets() }), Modifier.padding(horizontal = 48.dp))
    }
}

@Composable private fun ChannelRow(ch: Channel, meta: Meta?, at: Int, active: Boolean, modifier: Modifier, activate: () -> Unit) {
    Box(modifier.fillMaxWidth().testTag("neo.channel.$at").semantics { selected = active }.clickable(onClick = activate)) {
        if (active) Asset(R.drawable.selection_row, Modifier.fillMaxSize().padding(horizontal = 4.dp))
        Row(Modifier.fillMaxSize().border(.5.dp, Color(0xFF092333)).padding(horizontal = 14.dp), verticalAlignment = Alignment.CenterVertically) {
            TextLine("${at + 1}", 23, modifier = Modifier.width(65.dp), lines = 1)
            Picon(meta, Modifier.width(100.dp).fillMaxHeight().padding(4.dp)); Spacer(Modifier.width(22.dp))
            val programme = meta?.events?.firstOrNull()?.title ?: ch.current
            val label = remember(ch.name, programme, active) { buildAnnotatedString {
                withStyle(SpanStyle(color = Neo.white, fontSize = 23.sp)) { append(ch.name) }
                if (programme.isNotBlank()) withStyle(SpanStyle(color = if (active) Neo.white else Neo.epg)) {
                    append("   │   "); append(programme)
                }
            } }
            Text(label, modifier = Modifier.weight(1f).selectedMarquee(active).testTag("neo.channelText.$at"),
                fontSize = 24.sp, lineHeight = 28.sp, maxLines = 1, softWrap = false, overflow = TextOverflow.Clip)
            Spacer(Modifier.width(20.dp)); Progress(meta?.events?.firstOrNull()?.progress() ?: 0f, Modifier.width(98.dp)); Spacer(Modifier.width(36.dp))
        }
    }
}

@Composable private fun MainMenu(s: ReceiverUi) {
    Box(Modifier.fillMaxSize().testTag("neo.menu").background(Neo.bg), contentAlignment = Alignment.Center) {
        Column(Modifier.fillMaxWidth().padding(horizontal = 26.dp).height(516.dp).border(2.dp, Neo.line, RoundedCornerShape(14.dp)).padding(horizontal = 34.dp, vertical = 22.dp)) {
            Row(Modifier.height(84.dp).fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                TextLine("Vu⁺", 54, bold = true); Spacer(Modifier.width(28.dp)); Box(Modifier.height(32.dp).width(1.dp).background(Neo.line)); TextLine("Main Menu", 36, modifier = Modifier.padding(start = 24.dp).weight(1f)); WeatherClock(Modifier.width(1100.dp).height(82.dp))
            }
            Row(Modifier.fillMaxWidth().weight(1f), horizontalArrangement = Arrangement.spacedBy(14.dp)) {
                val titles = listOf("Plugin Browser", "Setup", "Timers", "Standby / Restart", "Information")
                val details = listOf("Plugins Enigma2", "Paramètres\nde connexion", "Programmations\ndu Vu+", "Veille de la TV", "Infos système\net télécommande")
                val icons = listOf(R.drawable.menu_plugins, R.drawable.menu_setup, R.drawable.menu_timers, R.drawable.menu_power, R.drawable.menu_info)
                titles.forEachIndexed { i, title -> MenuTile(s, i, title, details[i], icons[i], Modifier.weight(1f)) }
            }
            Spacer(Modifier.height(18.dp)); Footer(listOf("Quitter", "Satellites", "Liste des chaînes", "Télévision"), listOf({ s.back() }, { s.openSatellites() }, { s.page = "channels" }, { s.page = if (s.playing != null) "player" else "channels" }))
        }
    }
}
@Composable private fun MenuTile(s: ReceiverUi, at: Int, title: String, detail: String, icon: Int, modifier: Modifier) {
    val active by remember(s, at) { derivedStateOf { s.menuIndex == at } }
    val background = remember(active) { Brush.verticalGradient(if (active) listOf(Color(0xFF003389), Color(0xFF002B73)) else listOf(Color(0xFF0C2B47), Color(0xFF091E31))) }
    Column(modifier.fillMaxHeight().background(background).testTag("neo.menu.$at").semantics { selected = active }
        .border(if (active) 3.dp else 2.dp, if (active) Neo.cyan else Neo.line, RoundedCornerShape(7.dp))
        .clickable { s.menuIndex = at; s.activateMenu() }.padding(20.dp), horizontalAlignment = Alignment.CenterHorizontally) {
        Spacer(Modifier.height(20.dp)); Asset(icon, Modifier.size(104.dp)); Spacer(Modifier.height(24.dp)); TextLine(title, 31, lines = 1, bold = true)
        Spacer(Modifier.height(12.dp)); TextLine(detail, 25, Neo.muted, lines = 2)
    }
}
@Composable private fun Bouquets(s: ReceiverUi) {
    val isSat = s.page == "satellites"
    val names = remember(isSat, s.satellites, s.bouquets) { if (isSat) s.satellites.map { it.name } else s.bouquets }
    Column(Modifier.fillMaxSize().testTag(if (isSat) "neo.satellites" else "neo.bouquets").background(Neo.bg)) {
        Header(if (isSat) "Satellites" else "Bouquets TV")
        val start by remember(s) { derivedStateOf { s.bouquetIndex / 20 * 20 } }
        val rows = remember(names, start) { pageWindow(names, start) }
        Column(Modifier.weight(1f).padding(horizontal = 48.dp).border(1.dp, Neo.line)) {
            rows.forEachIndexed { offset, name -> GroupRow(s, name, start + offset, isSat, Modifier.weight(1f)) }
            repeat(20 - rows.size) { Spacer(Modifier.weight(1f)) }
        }
        Footer(listOf("Tous les services", "Satellites", "← → : page", "Bouquets"), listOf({ s.chooseBouquet("") }, { s.openSatellites() }, {}, { s.openBouquets() }), Modifier.padding(horizontal = 48.dp))
    }
}

@Composable private fun GroupRow(s: ReceiverUi, name: String, at: Int, isSatellite: Boolean, modifier: Modifier) {
    Box(modifier.fillMaxWidth().testTag("neo.group.$at").semantics { selected = s.bouquetIndex == at }.clickable { s.bouquetIndex = at; s.selectGroup() }) {
        Asset(R.drawable.selection_row, Modifier.matchParentSize().graphicsLayer { alpha = if (s.bouquetIndex == at) 1f else 0f })
        Row(Modifier.fillMaxSize().padding(horizontal = 24.dp), verticalAlignment = Alignment.CenterVertically) {
            TextLine("${at + 1}", 24, modifier = Modifier.width(85.dp)); TextLine(name, 28, modifier = Modifier.weight(1f), lines = 1)
            if (!isSatellite) TextLine("${s.bouquetSize(name)} services", 24, Neo.muted)
        }
    }
}

@androidx.annotation.OptIn(androidx.media3.common.util.UnstableApi::class)
@Composable private fun Infobar(s: ReceiverUi) {
    val ch = s.playing ?: return; val m = s.meta[ch.ref]; val p = m?.events?.firstOrNull()
    Box(Modifier.fillMaxSize()) {
        WeatherClock(Modifier.align(Alignment.TopCenter).padding(top = 25.dp).width(1850.dp).height(122.dp))
        Text(ch.name, color = Neo.white, fontFamily = FontFamily(Font(R.font.raleway_light)), fontSize = 112.sp, maxLines = 1, overflow = TextOverflow.Ellipsis,
            modifier = Modifier.align(Alignment.BottomStart).padding(start = 80.dp, end = 80.dp, bottom = 248.dp))
        Column(Modifier.align(Alignment.BottomCenter).fillMaxWidth().height(248.dp).background(Neo.panel.copy(alpha = .97f)).border(1.dp, Neo.cyan).padding(horizontal = 46.dp, vertical = 22.dp)) {
            Row(Modifier.weight(1f), verticalAlignment = Alignment.CenterVertically) {
                TextLine("%03d".format((s.visible.indexOfFirst { it.ref == ch.ref } + 1).coerceAtLeast(1)), 43, modifier = Modifier.width(94.dp)); Picon(m, Modifier.width(150.dp).height(92.dp)); Spacer(Modifier.width(28.dp))
                Column(Modifier.weight(1f)) {
                    TextLine(p?.title ?: "EPG indisponible", 34, lines = 1); TextLine(p?.description?.lineSequence()?.firstOrNull().orEmpty(), 23, Neo.muted, lines = 1); Spacer(Modifier.height(12.dp))
                    Row(verticalAlignment = Alignment.CenterVertically) { TextLine(p?.let { time(it.begin) } ?: "--:--", 24); Spacer(Modifier.width(20.dp)); Progress(p?.progress() ?: 0f, Modifier.weight(1f)); Spacer(Modifier.width(20.dp)); TextLine(p?.let { time(it.begin + it.duration) } ?: "--:--", 24) }
                }
                Spacer(Modifier.width(36.dp)); Box(Modifier.height(108.dp).width(1.dp).background(Neo.line)); Spacer(Modifier.width(24.dp))
                Column(Modifier.width(430.dp)) { TextLine("Suivant : " + (m?.events?.getOrNull(1)?.title ?: "non disponible"), 24, lines = 2); m?.events?.getOrNull(1)?.let { TextLine("${time(it.begin)} – ${time(it.begin + it.duration)}", 23, Neo.muted) } }
            }
            Spacer(Modifier.height(16.dp)); Box(Modifier.fillMaxWidth().height(1.dp).background(Neo.line)); Spacer(Modifier.height(16.dp))
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                val f = s.videoFormat; val a = s.audioFormat
                val facts = listOf(if ((f?.height ?: 0) >= 2160) "4K" else if ((f?.height ?: 0) >= 1080) "FHD" else if (f != null) "HD / SD" else "RES —",
                    if (f?.colorInfo?.colorTransfer in listOf(6, 7)) "HDR" else "HDR —", a?.sampleMimeType?.removePrefix("audio/")?.uppercase() ?: "AUDIO —",
                    f?.sampleMimeType?.removePrefix("video/")?.uppercase() ?: "CODEC —", "CRYPT —", if (ch.ref.startsWith("1:")) "DVB" else "IPTV",
                    if (f != null) "${f.width} × ${f.height}" else "— × —", if (f != null && f.frameRate > 0) "${"%.2f".format(f.frameRate)} fps" else "FPS —",
                    "ASPECT —", a?.language?.uppercase() ?: "LANG —", "REC —", "TUNER —", "TIMESHIFT —", "SNR / AGC —")
                facts.forEach { TextLine(it, 18, if (it.contains('—')) Neo.muted.copy(alpha = .55f) else Neo.white, Modifier.weight(1f), lines = 1) }
            }
        }
    }
}
@Composable private fun Guide(s: ReceiverUi) {
    val ch = s.selected; val events = ch?.let { s.meta[it.ref]?.events }.orEmpty(); val at = s.detailIndex.coerceAtMost((events.size - 1).coerceAtLeast(0))
    Column(Modifier.fillMaxSize().testTag("neo.guide").background(Neo.bg)) {
        Header("Guide TV - " + (ch?.name ?: "Aucune chaîne"))
        Row(Modifier.weight(1f).padding(48.dp), horizontalArrangement = Arrangement.spacedBy(32.dp)) {
            Column(Modifier.weight(1.1f).fillMaxHeight()) {
                if (events.isEmpty()) TextLine("EPG indisponible pour cette chaîne", 30, Neo.muted)
                events.drop(at / 10 * 10).take(10).forEachIndexed { offset, p -> val i = at / 10 * 10 + offset
                    Row(Modifier.fillMaxWidth().height(74.dp).background(if (i == at) Color(0xFF003F9F) else Neo.panel).clickable { s.detailIndex = i }, verticalAlignment = Alignment.CenterVertically) {
                        TextLine("${time(p.begin)} – ${time(p.begin + p.duration)}", 24, Neo.cyan, Modifier.width(210.dp).padding(start = 14.dp))
                        Text(p.title, modifier = Modifier.weight(1f).selectedMarquee(i == at), color = Neo.white,
                            fontSize = 27.sp, lineHeight = 32.sp, maxLines = 1, softWrap = false, overflow = TextOverflow.Clip)
                    }
                }
            }
            Column(Modifier.weight(1f).fillMaxHeight().border(1.dp, Neo.line).padding(32.dp)) { TextLine(events.getOrNull(at)?.title.orEmpty(), 40); Spacer(Modifier.height(24.dp)); TextLine(events.getOrNull(at)?.description.orEmpty(), 28, Neo.muted, lines = 20) }
        }
        Footer(listOf("Liste des chaînes", "OK : regarder", "← → : chaîne", "Bouquets"), listOf({ s.page = "channels" }, { ch?.let { s.play(it) } }, {}, { s.openBouquets() }), Modifier.padding(horizontal = 48.dp))
    }
}
@Composable private fun DetailPage(title: String, body: String) {
    Column(Modifier.fillMaxSize().testTag("neo.details").background(Neo.bg)) { Header(title); TextLine(body, 29, Neo.white, Modifier.padding(60.dp).weight(1f), 24); TextLine("EXIT : retour", 25, Neo.cyan, Modifier.padding(48.dp)) }
}
@Composable private fun Tracks(s: ReceiverUi) {
    val tracks = s.tracks()
    Column(Modifier.fillMaxSize().testTag("neo.tracks").background(Neo.bg)) {
        Header("Pistes audio et sous-titres")
        tracks.forEachIndexed { i, t -> Box(Modifier.fillMaxWidth().height(72.dp).padding(horizontal = 48.dp).background(if (i == s.detailIndex) Color(0xFF003F9F) else Neo.panel).clickable { s.selectTrack(i) }.padding(18.dp)) { TextLine(t.third, 28, lines = 1) } }
        Spacer(Modifier.weight(1f)); TextLine("↑↓ : choisir   •   OK : appliquer   •   EXIT : retour", 26, Neo.cyan, Modifier.padding(48.dp))
    }
}
@Composable private fun Settings(s: ReceiverUi) {
    val context = LocalContext.current
    val playerFocus = remember { FocusRequester() }
    LaunchedEffect(Unit) { playerFocus.requestFocus() }
    var host by remember(s.settings) { mutableStateOf(s.settings.host) }; var port by remember(s.settings) { mutableStateOf(s.settings.port.toString()) }
    var username by remember { mutableStateOf(s.settings.username) }; var password by remember { mutableStateOf(s.settings.password) }
    Column(Modifier.fillMaxSize().testTag("neo.settings").background(Neo.bg)) {
        Header("Setup - Connexion Vu+")
        Column(Modifier.padding(horizontal = 160.dp, vertical = 35.dp)) {
            TextLine("OpenWebif • réseau local • lecture seule", 32, Neo.muted); Spacer(Modifier.height(18.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(24.dp), verticalAlignment = Alignment.CenterVertically) {
                TextLine("Lecteur vidéo", 28, Neo.muted)
                s.engines.forEach { engine ->
                    var focused by remember { mutableStateOf(false) }
                    Button(onClick = { s.selectEngine(engine) }, modifier =
                        (if (s.engine == engine) Modifier.focusRequester(playerFocus) else Modifier)
                            .onFocusChanged { focused = it.isFocused }
                            .border(3.dp, if (focused) Neo.white else Color.Transparent, RoundedCornerShape(38.dp))) {
                        TextLine(engine + if (s.engine == engine) "  ✓" else "", 27)
                    }
                }
                Button(onClick = { context.startActivity(Intent(context, com.metrixneo.tv.connect.NeoConnectActivity::class.java)) }, modifier = Modifier.testTag("neo.connect.open")) {
                    TextLine("Neo Connect", 27)
                }
            }
            Spacer(Modifier.height(22.dp))
            val style = androidx.compose.ui.text.TextStyle(fontSize = 30.sp, color = Neo.white)
            Row(horizontalArrangement = Arrangement.spacedBy(32.dp)) {
                OutlinedTextField(host, { host = it }, Modifier.weight(2f), label = { TextLine("Adresse IP du Vu+", 24) }, textStyle = style, singleLine = true)
                OutlinedTextField(port, { port = it }, Modifier.weight(1f), label = { TextLine("Port", 24) }, textStyle = style, singleLine = true)
            }
            Spacer(Modifier.height(28.dp)); Row(horizontalArrangement = Arrangement.spacedBy(32.dp)) {
                OutlinedTextField(username, { username = it }, Modifier.weight(1f), label = { TextLine("Utilisateur (optionnel)", 24) }, textStyle = style, singleLine = true)
                OutlinedTextField(password, { password = it }, Modifier.weight(1f), label = { TextLine("Mot de passe", 24) }, textStyle = style, visualTransformation = PasswordVisualTransformation(), singleLine = true)
            }
            Spacer(Modifier.height(36.dp)); Button(onClick = { s.connect(ReceiverSettings(host.trim(), port.toInt(), username, password)) }, enabled = !s.busy && (port.toIntOrNull() ?: 0) in 1..65535, modifier = Modifier.height(76.dp)) { TextLine(if (s.busy) "Connexion…" else "Enregistrer et charger les bouquets", 28) }
            Spacer(Modifier.height(30.dp)); TextLine(s.status, 28, Neo.cyan, lines = 3); Spacer(Modifier.height(24.dp)); TextLine("Connexion et bouquet mémorisés. Le mot de passe est chiffré avec une clé Android propre à cette TV.", 25, Neo.muted)
        }
    }
}
