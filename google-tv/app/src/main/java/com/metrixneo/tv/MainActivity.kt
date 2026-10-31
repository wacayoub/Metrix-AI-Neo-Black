package com.metrixneo.tv

import android.os.Bundle
import android.view.KeyEvent
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.media3.common.MediaItem
import androidx.media3.common.PlaybackException
import androidx.media3.common.Player
import androidx.media3.common.VideoSize
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.ui.PlayerView
import kotlinx.coroutines.launch

private object Neo {
    val bg=Color(0xFF040D1B)
    val glass=Color(0xF00A1B33)
    val cyan=Color(0xFF27CBFF)
    val blue=Color(0xFF178BFF)
    val txt=Color(0xFFF1F7FF)
    val faint=Color(0xFF99AEC8)
    val line=Color(0xFF214C78)
    val good=Color(0xFF46E4A1)
}
private val cardShape=RoundedCornerShape(16.dp)

@Composable private fun Backdrop(body:@Composable ()->Unit){
    Box(Modifier.fillMaxSize().background(Brush.linearGradient(listOf(Color(0xFF082954),Neo.bg,Color(0xFF020712))))){body()}
}
@Composable private fun Caption(value:String, modifier:Modifier=Modifier, color:Color=Neo.faint, size:Int=13){
    Text(value,modifier=modifier,color=color,fontSize=size.sp,maxLines=3,overflow=TextOverflow.Ellipsis)
}
@Composable private fun Panel(modifier:Modifier=Modifier, action:(()->Unit)?=null, content:@Composable ColumnScope.()->Unit){
    var focused by remember{mutableStateOf(false)}
    var m=modifier.clip(cardShape)
        .background(Brush.verticalGradient(listOf(if(focused) Color(0xFF13508B) else Neo.glass,Color(0xF0081428))))
        .border(if(focused) 2.dp else 1.dp, if(focused) Neo.cyan else Neo.line,cardShape)
    if(action!=null) m=m.onFocusChanged{focused=it.isFocused}.clickable(onClick=action)
    Column(m.padding(16.dp),content=content)
}
@Composable private fun Heading(title:String,sub:String=""){
    Text(title,color=Neo.txt,fontSize=22.sp,fontWeight=FontWeight.Bold)
    if(sub.isNotBlank()) Caption(sub)
}
@Composable private fun MenuTile(symbol:String,title:String,description:String,modifier:Modifier=Modifier,onClick:()->Unit){
    Panel(modifier,action=onClick){
        Spacer(Modifier.weight(1f))
        Text(symbol,color=Neo.cyan,fontSize=39.sp,fontWeight=FontWeight.Bold)
        Spacer(Modifier.weight(1f))
        Text(title,color=Neo.txt,fontSize=20.sp,fontWeight=FontWeight.Bold)
        Caption(description,size=12)
    }
}
@Composable private fun Header(page:String,connected:Boolean){
    Row(Modifier.fillMaxWidth().padding(horizontal=25.dp,vertical=10.dp),verticalAlignment=Alignment.CenterVertically){
        Text("METRIX",color=Neo.txt,fontSize=25.sp,fontWeight=FontWeight.Black)
        Text(" NEO",color=Neo.cyan,fontSize=25.sp,fontWeight=FontWeight.Black)
        Text(" AI",color=Color(0xFFB4A2FF),fontSize=22.sp)
        Spacer(Modifier.width(26.dp))
        Caption(page.uppercase())
        Spacer(Modifier.weight(1f))
        Caption(if(connected) "● Vu+ connecté" else "○ Pas de connexion",color=if(connected)Neo.good else Neo.faint)
        Spacer(Modifier.width(22.dp))
        Caption("Google TV",color=Neo.txt,size=15)
    }
}
private data class AppState(val channels:List<TvChannel> = emptyList(), val status:String="Non connecté",val online:Boolean=false,val latency:Long?=null)

class MainActivity: ComponentActivity(){
    override fun onCreate(savedInstanceState:Bundle?){
        super.onCreate(savedInstanceState)
        val prefs=getSharedPreferences("receiver",MODE_PRIVATE)
        setContent{
            var page by remember { mutableStateOf("home") }
            var config by remember { mutableStateOf(ReceiverSettings(
                host=prefs.getString("host","192.168.11.2") ?: "192.168.11.2",
                port=prefs.getInt("port",80),
                user=prefs.getString("user","") ?: "",
                secure=prefs.getBoolean("secure",false)
            )) }
            var status by remember{mutableStateOf(AppState())}
            var loading by remember{mutableStateOf(false)}
            var playing by remember{mutableStateOf<TvChannel?>(null)}
            var stream by remember{mutableStateOf<String?>(null)}
            var streamError by remember{mutableStateOf("")}
            val scope=rememberCoroutineScope()
            val client=remember(config){OpenWebif(config)}
            fun back(){page=if(page=="player")"channels" else "home"}
            BackHandler(page!="home"){back()}
            Backdrop{
                Column{
                    if(page!="player")Header(page,status.online)
                    Box(Modifier.weight(1f)){
                        when(page){
                            "home"->Home(status){page=it}
                            "channels"->ChannelList(status.channels,onPlay={ ch->
                                playing=ch; stream=null; streamError="Connexion au flux…"; page="player"
                                scope.launch {
                                    try {stream=client.playlistStream(ch.reference);streamError=""}
                                    catch(t:Exception){streamError=t.message ?: "Flux indisponible"}
                                }
                            },onSettings={page="settings"})
                            "epg"->EpgPage(status.channels,onTune={ch->playing=ch;stream=null;streamError="Connexion au flux…";page="player";scope.launch{try{stream=client.playlistStream(ch.reference);streamError=""}catch(t:Exception){streamError=t.message ?: "Flux indisponible"}}})
                            "settings"->Settings(config,status.status,loading){newSettings->
                                loading=true; status=status.copy(status="Connexion…",online=false)
                                scope.launch {
                                    val c=OpenWebif(newSettings)
                                    try {
                                        val latency=c.ping()
                                        val loaded=c.loadChannels()
                                        if(loaded.isEmpty()) error("Aucune chaîne récupérée; vérifier les bouquets OpenWebif")
                                        config=newSettings
                                        prefs.edit().putString("host",config.host).putInt("port",config.port)
                                            .putString("user",config.user).putBoolean("secure",config.secure).apply()
                                        status=AppState(loaded,"${loaded.size} chaînes synchronisées",true,latency)
                                        page="channels"
                                    } catch(t:Exception){status=AppState(status=t.message ?: "Connexion impossible")}
                                    finally{loading=false}
                                }
                            }
                            "health"->Health(status,onConfig={page="settings"})
                            "player"->playing?.let { ch->
                                LivePlayer(ch,stream,streamError,onBack={back()})
                            }
                            else->Home(status){page=it}
                        }
                    }
                }
            }
        }
    }
}
@Composable private fun Home(state:AppState,navigate:(String)->Unit){
    Column(Modifier.fillMaxSize().padding(horizontal=25.dp,vertical=14.dp)){
        Text("LA TÉLÉVISION NOUVELLE GÉNÉRATION",fontSize=12.sp,color=Neo.cyan)
        Text("Metrix NEO AI",fontSize=42.sp,color=Neo.txt,fontWeight=FontWeight.Black)
        Caption("Le véritable esprit Metrix NEO sur Google TV · aperçu de développement")
        Spacer(Modifier.height(20.dp))
        Row(Modifier.fillMaxWidth().height(205.dp),horizontalArrangement=Arrangement.spacedBy(12.dp)){
            MenuTile("▣","TV en direct","Chaînes du Vu+",Modifier.weight(1f)){navigate("channels")}
            MenuTile("◉","Bouquets","Services synchronisés",Modifier.weight(1f)){navigate("channels")}
            MenuTile("▦","Guide TV","EPG disponible",Modifier.weight(1f)){navigate("epg")}
            MenuTile("▶","Enregistrements","Prochaine version",Modifier.weight(1f)){navigate("health")}
            MenuTile("⚙","Paramètres","Connexion & réglages",Modifier.weight(1f)){navigate("settings")}
        }
        Spacer(Modifier.height(20.dp))
        Row(Modifier.fillMaxWidth().weight(1f),horizontalArrangement=Arrangement.spacedBy(12.dp)){
            Panel(Modifier.weight(1.25f).fillMaxHeight(),action={navigate("channels")}){
                Heading("Reprendre la TV","Sélection rapide")
                Spacer(Modifier.height(16.dp))
                if(state.online) {
                    state.channels.take(4).forEach{ch->Caption("▸  ${ch.name}",Modifier.padding(vertical=7.dp),Neo.txt,16)}
                } else Caption("Connecte ton Vu+ depuis Paramètres pour obtenir tes vrais bouquets.",size=17)
            }
            Panel(Modifier.weight(1f).fillMaxHeight(),action={navigate("epg")}){
                Heading("Guide des programmes","En direct et ensuite")
                Spacer(Modifier.height(14.dp))
                Caption("EPG : ${if(state.online) "titres disponibles dans les bouquets" else "connexion nécessaire"}",size=16)
            }
            Panel(Modifier.weight(1f).fillMaxHeight(),action={navigate("health")}){
                Heading("Diagnostic intelligent","Analyse locale et transparente")
                Spacer(Modifier.height(15.dp))
                Caption(if(state.online) "● En ligne" else "○ Hors ligne",color=if(state.online) Neo.good else Neo.faint,size=18)
                Caption(state.latency?.let{"API : $it ms"} ?: "Mesure API indisponible")
                Caption(state.status,size=13)
            }
        }
        Spacer(Modifier.height(10.dp))
        Caption("NEO AI 0.2 ALPHA • Navigation OK / RETOUR • Intelligence avancée : en développement",size=11)
    }
}
@Composable private fun ChannelRow(channel:TvChannel,index:Int,onClick:()->Unit){
    Panel(Modifier.fillMaxWidth(),action=onClick){
        Row(verticalAlignment=Alignment.CenterVertically){
            Caption("%04d".format(index+1),Modifier.width(65.dp),Neo.cyan,13)
            Column(Modifier.weight(1f)){
                Text(channel.name,color=Neo.txt,fontWeight=FontWeight.SemiBold,fontSize=17.sp,maxLines=1)
                Caption(channel.bouquet + if(channel.now.isNotBlank())"  ·  "+channel.now else "")
            }
            Text("▶",color=Neo.cyan)
        }
    }
}
@Composable private fun ChannelList(channels:List<TvChannel>,onPlay:(TvChannel)->Unit,onSettings:()->Unit){
    Column(Modifier.fillMaxSize().padding(horizontal=24.dp,vertical=12.dp)){
        Heading("Chaînes & Bouquets",if(channels.isEmpty())"Aucune chaîne connectée" else "${channels.size} chaînes du Vu+")
        Spacer(Modifier.height(14.dp))
        if(channels.isEmpty()) {
            Panel(Modifier.fillMaxWidth(),action=onSettings){
                Heading("Connecter mon Vu+","Utiliser OpenWebif en lecture seule")
                Caption("Ouvrir les paramètres de connexion",color=Neo.cyan)
            }
        } else {
            var group by remember(channels){mutableStateOf("Toutes")}
            val groups=remember(channels){listOf("Toutes")+channels.map{it.bouquet}.distinct()}
            val filtered=remember(channels,group){if(group=="Toutes")channels else channels.filter{it.bouquet==group}}
            Row(Modifier.fillMaxSize(),horizontalArrangement=Arrangement.spacedBy(14.dp)){
                Panel(Modifier.width(215.dp).fillMaxHeight()){
                    Heading("Bouquets")
                    Spacer(Modifier.height(12.dp))
                    LazyColumn(verticalArrangement=Arrangement.spacedBy(5.dp)){
                        itemsIndexed(groups){_,item->
                            FocusLine(item,selected=group==item){group=item}
                        }
                    }
                }
                Panel(Modifier.weight(1f).fillMaxHeight()){
                    Heading("Toutes les chaînes","${filtered.size} résultats")
                    Spacer(Modifier.height(10.dp))
                    LazyColumn(verticalArrangement=Arrangement.spacedBy(7.dp)){
                        itemsIndexed(filtered){i,ch->ChannelRow(ch,i){onPlay(ch)}}
                    }
                }
                Panel(Modifier.width(250.dp).fillMaxHeight()){
                    Heading("METRIX NEO","LIVE TV")
                    Spacer(Modifier.height(18.dp))
                    Caption("OK : lire la chaîne sélectionnée",color=Neo.cyan,size=16)
                    Spacer(Modifier.height(14.dp))
                    Caption("La liste vient exclusivement d’OpenWebif. Aucun titre ou horaire n’est inventé.")
                }
            }
        }
    }
}
@Composable private fun FocusLine(title:String,selected:Boolean,onClick:()->Unit){
    var focused by remember {mutableStateOf(false)}
    Row(Modifier.fillMaxWidth().clip(RoundedCornerShape(8.dp))
        .background(if(focused||selected)Color(0xFF145497)else Color.Transparent)
        .onFocusChanged{focused=it.isFocused}.clickable(onClick=onClick)
        .padding(10.dp)){
        Caption(title,color=if(focused||selected)Neo.txt else Neo.faint,size=15)
    }
}
@Composable private fun EpgPage(channels:List<TvChannel>,onTune:(TvChannel)->Unit){
    Column(Modifier.fillMaxSize().padding(24.dp)){
        Heading("Guide TV • EPG","Titres issus d’OpenWebif lorsque disponibles · chronologie complète à développer")
        Spacer(Modifier.height(16.dp))
        if(channels.isEmpty()) Caption("Connecte ton Vu+ pour afficher les programmes.")
        else LazyColumn(verticalArrangement=Arrangement.spacedBy(7.dp)){
            itemsIndexed(channels){_,ch->
                Panel(Modifier.fillMaxWidth(),action={onTune(ch)}){
                    Row(verticalAlignment=Alignment.CenterVertically){
                        Text(ch.name,Modifier.weight(1f),fontSize=16.sp,color=Neo.txt)
                        Caption(ch.now.ifBlank{"EPG indisponible"},Modifier.weight(2f),Neo.cyan,15)
                        Caption(ch.next.ifBlank{"Programme suivant indisponible"},Modifier.weight(2f),Neo.faint,14)
                    }
                }
            }
        }
    }
}
@Composable private fun Health(status:AppState,onConfig:()->Unit){
    Column(Modifier.fillMaxSize().padding(24.dp)){
        Heading("NEO AI • Diagnostic","Diagnostic factuel : aucune analyse externe et aucune modification du Vu+")
        Spacer(Modifier.height(20.dp))
        Row(horizontalArrangement=Arrangement.spacedBy(16.dp)){
            Panel(Modifier.weight(1f).height(205.dp)){
                Heading("Connectivité")
                Spacer(Modifier.height(18.dp))
                Caption(status.status,color=if(status.online) Neo.good else Neo.faint,size=17)
                Caption(status.latency?.let{"Latence API $it ms"} ?: "Aucune latence mesurée")
            }
            Panel(Modifier.weight(1f).height(205.dp)){
                Heading("Bouquets")
                Spacer(Modifier.height(18.dp))
                Text("${status.channels.size}",fontSize=33.sp,color=Neo.cyan)
                Caption("Chaînes récupérées")
            }
            Panel(Modifier.weight(1f).height(205.dp)){
                Heading("Intelligence avancée")
                Spacer(Modifier.height(18.dp))
                Caption("Recommandations et détection proactive : non implémentées.",size=16)
            }
        }
        Spacer(Modifier.height(25.dp))
        Button(onClick=onConfig){Text("Configurer le Vu+")}
    }
}
@Composable private fun Settings(saved:ReceiverSettings,status:String,busy:Boolean,connect:(ReceiverSettings)->Unit){
    var host by remember(saved.host){mutableStateOf(saved.host)}
    var port by remember(saved.port){mutableStateOf(saved.port.toString())}
    var user by remember(saved.user){mutableStateOf(saved.user)}
    var pass by remember {mutableStateOf("")}
    var secure by remember(saved.secure){mutableStateOf(saved.secure)}
    Column(Modifier.fillMaxSize().padding(26.dp)){
        Heading("Connexion au Vu+","OpenWebif · lecture seule · aucune commande Enigma2")
        Spacer(Modifier.height(18.dp))
        Row(horizontalArrangement=Arrangement.spacedBy(18.dp)){
            Column(Modifier.weight(1f),verticalArrangement=Arrangement.spacedBy(12.dp)){
                OutlinedTextField(host,{host=it},label={Text("Adresse IP du récepteur")},singleLine=true,modifier=Modifier.fillMaxWidth())
                OutlinedTextField(port,{port=it},label={Text("Port OpenWebif")},singleLine=true,
                    keyboardOptions=KeyboardOptions(keyboardType=KeyboardType.Number),modifier=Modifier.fillMaxWidth())
                Row(verticalAlignment=Alignment.CenterVertically){
                    Text("HTTPS",color=Neo.txt)
                    Spacer(Modifier.width(16.dp))
                    Switch(checked=secure,onCheckedChange={secure=it})
                }
            }
            Column(Modifier.weight(1f),verticalArrangement=Arrangement.spacedBy(12.dp)){
                OutlinedTextField(user,{user=it},label={Text("Utilisateur (facultatif)")},singleLine=true,modifier=Modifier.fillMaxWidth())
                OutlinedTextField(pass,{pass=it},label={Text("Mot de passe — jamais sauvegardé")},
                    singleLine=true,visualTransformation=PasswordVisualTransformation(),modifier=Modifier.fillMaxWidth())
                Caption("HTTP réservé au réseau privé. N’expose jamais OpenWebif sur Internet.")
            }
        }
        Spacer(Modifier.height(20.dp))
        Button(enabled=!busy && host.isNotBlank() && (port.toIntOrNull() ?: 0) in 1..65535,
            onClick={connect(ReceiverSettings(host.trim(),port.toInt(),user,pass,secure))}){
            Text(if(busy)"Synchronisation..." else "Tester et synchroniser")
        }
        Spacer(Modifier.height(14.dp))
        Caption(status,color=Neo.txt,size=16)
    }
}
@Composable private fun LivePlayer(channel:TvChannel,stream:String?,error:String,onBack:()->Unit){
    val context=LocalContext.current
    var playback by remember(stream){mutableStateOf("Connexion…")}
    var videoWidth by remember(stream){mutableIntStateOf(0)}
    var videoHeight by remember(stream){mutableIntStateOf(0)}
    val player=remember(stream){
        if(stream.isNullOrBlank()) null else ExoPlayer.Builder(context).build().apply{
            setMediaItem(MediaItem.fromUri(stream))
            prepare()
            playWhenReady=true
        }
    }
    DisposableEffect(player){
        if(player==null) onDispose {} else {
            val callback=object:Player.Listener{
                override fun onPlaybackStateChanged(state:Int){
                    playback=when(state){
                        Player.STATE_BUFFERING->"Mise en mémoire tampon"
                        Player.STATE_READY->"En direct"
                        Player.STATE_ENDED->"Fin du flux"
                        else->"Connexion…"
                    }
                }
                override fun onPlayerError(error:PlaybackException){playback="Erreur ${error.errorCodeName}"}
                override fun onVideoSizeChanged(size:VideoSize){videoWidth=size.width;videoHeight=size.height}
            }
            player.addListener(callback)
            onDispose {player.removeListener(callback);player.release()}
        }
    }
    Box(Modifier.fillMaxSize().background(Color.Black)){
        if(player!=null) AndroidView(factory={ctx->PlayerView(ctx).apply{this.player=player;useController=false}},
            modifier=Modifier.fillMaxSize())
        else Column(Modifier.align(Alignment.Center),horizontalAlignment=Alignment.CenterHorizontally){
            Text("METRIX NEO AI",color=Neo.cyan,fontSize=36.sp)
            Spacer(Modifier.height(12.dp))
            Caption(error.ifBlank{"Recherche du flux…"},size=17)
        }
        Column(Modifier.align(Alignment.BottomCenter).fillMaxWidth()
            .padding(horizontal=25.dp,vertical=16.dp).clip(cardShape)
            .background(Neo.glass).border(1.dp,Neo.line,cardShape).padding(14.dp)){
            Text(channel.name,color=Neo.txt,fontSize=24.sp,fontWeight=FontWeight.Bold)
            Row(verticalAlignment=Alignment.CenterVertically){
                Column(Modifier.weight(1f)){
                    Text(channel.now.ifBlank{"Programme indisponible"},color=Neo.cyan,fontSize=17.sp)
                    Caption("Ensuite : "+channel.next.ifBlank{"Non renseigné"},size=13)
                }
                Column(horizontalAlignment=Alignment.End){
                    Caption(playback,color=Neo.good,size=14)
                    Caption(if(videoWidth>0)"$videoWidth × $videoHeight" else "Résolution indisponible")
                }
            }
            Spacer(Modifier.height(9.dp))
            Row(horizontalArrangement=Arrangement.spacedBy(5.dp)){
                val labels=listOf("UHD","HDR","HEVC","DOLBY","AC3","16:9","TXT","SUB","AUD","REC","SAT","IPTV","SNR","AGC")
                labels.forEach{label->
                    val active=label=="UHD" && videoWidth>=3840
                    Box(Modifier.border(1.dp,if(active)Neo.cyan else Neo.line,RoundedCornerShape(4.dp))
                        .padding(horizontal=6.dp,vertical=4.dp)){
                        Caption(label,color=if(active)Neo.cyan else Neo.faint,size=10)
                    }
                }
            }
            Spacer(Modifier.height(6.dp))
            Caption("Indicateurs non mesurés = neutres • RETOUR : chaînes",size=10)
        }
    }
}
