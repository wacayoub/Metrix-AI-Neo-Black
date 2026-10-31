package com.metrixneo.tv

import android.util.Base64
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.Inet4Address
import java.net.InetAddress
import java.net.URL
import java.net.URLEncoder

/** Requête OpenWebif strictement read-only. */
data class ReceiverSettings(
    val host:String="192.168.11.2",val port:Int=80,val user:String="",
    val password:String="",val secure:Boolean=false
)
data class TvChannel(val name:String,val reference:String,val bouquet:String="TV",val now:String="",val next:String="")
class OpenWebif(private val cfg:ReceiverSettings){
    private val base get()="${if(cfg.secure)"https" else "http"}://${cfg.host}:${cfg.port}"
    private fun lanAddress(host:String):Boolean{
        val a=InetAddress.getByName(host)
        return a is Inet4Address && (a.isSiteLocalAddress || a.isLoopbackAddress || a.isLinkLocalAddress)
    }
    private fun validate(){
        require(cfg.port in 1..65535){"Port invalide"}
        require(cfg.host.matches(Regex("[a-zA-Z0-9.-]{1,253}"))){"Adresse invalide"}
        if(!cfg.secure)require(lanAddress(cfg.host)){"HTTP réservé aux adresses LAN privées"}
    }
    private fun request(path:String):String{
        validate()
        val url=URL(base+path)
        val c=url.openConnection() as HttpURLConnection
        c.connectTimeout=4500
        c.readTimeout=6500
        c.instanceFollowRedirects=false
        c.setRequestProperty("Accept","application/json, text/plain, */*")
        if(cfg.user.isNotBlank()){
            val token=Base64.encodeToString("${cfg.user}:${cfg.password}".toByteArray(),Base64.NO_WRAP)
            c.setRequestProperty("Authorization","Basic $token")
        }
        try{
            val code=c.responseCode
            require(code in 200..299){"OpenWebif HTTP $code"}
            return c.inputStream.bufferedReader(Charsets.UTF_8).use{it.readText()}
        }finally{c.disconnect()}
    }
    suspend fun ping():Long=withContext(Dispatchers.IO){
        val start=System.nanoTime()
        val data=JSONObject(request("/api/about"))
        if(!data.has("info") && !data.has("result") && !data.has("enigma2"))error("Réponse OpenWebif non reconnue")
        (System.nanoTime()-start)/1_000_000
    }
    suspend fun loadChannels():List<TvChannel>=withContext(Dispatchers.IO){
        val list=ArrayList<TvChannel>()
        val seen=HashSet<String>()
        fun walk(node:Any?,bouquet:String,depth:Int){
            if(depth>8)return
            when(node){
                is JSONArray->for(i in 0 until node.length())walk(node.opt(i),bouquet,depth+1)
                is JSONObject->{
                    val name=node.optString("servicename",node.optString("name",""))
                    val ref=node.optString("servicereference",node.optString("sref",node.optString("reference","")))
                    val children=listOf("services","subservices","channels").firstNotNullOfOrNull{node.optJSONArray(it)}
                    if(children!=null)walk(children,name.ifBlank{bouquet},depth+1)
                    else if(name.isNotBlank() && ref.isNotBlank() && !seen.contains(ref)){
                        val flag=ref.split(':').getOrNull(1)?.toIntOrNull() ?: 0
                        if(flag and 64==0 && flag and 256==0){
                            seen.add(ref)
                            list.add(TvChannel(name,ref,bouquet,node.optString("eventtitle",node.optString("now_title","")),node.optString("next_title","")))
                        }
                    }
                }
            }
        }
        try{
            val root=JSONObject(request("/api/getallservices"))
            walk(root.optJSONArray("services") ?: root.optJSONArray("bouquets"),"TV",0)
        }catch(_:Exception){}
        if(list.isEmpty()){
            val root=JSONObject(request("/api/getservices"))
            val bouquets=root.optJSONArray("services") ?: JSONArray()
            for(i in 0 until bouquets.length()){
                val bouquet=bouquets.optJSONObject(i) ?: continue
                val ref=bouquet.optString("servicereference")
                if(ref.isBlank())continue
                try{
                    val children=JSONObject(request("/api/getservices?sRef="+URLEncoder.encode(ref,"UTF-8")))
                    walk(children.optJSONArray("services"),bouquet.optString("servicename","TV"),0)
                }catch(_:Exception){}
            }
        }
        list
    }
    suspend fun playlistStream(ref:String):String=withContext(Dispatchers.IO){
        require(ref.isNotBlank()){"Référence de chaîne manquante"}
        val content=request("/web/stream.m3u?ref="+URLEncoder.encode(ref,"UTF-8"))
        val raw=content.lineSequence().map{it.trim()}.firstOrNull{it.startsWith("http://")||it.startsWith("https://")}
            ?: error("Playlist OpenWebif vide")
        val uri=URL(raw)
        require(uri.protocol=="http"||uri.protocol=="https"){"Protocole non autorisé"}
        val host=if(uri.host=="127.0.0.1"||uri.host=="localhost")cfg.host else uri.host
        require(lanAddress(host)){"La source du flux ne pointe pas sur le LAN privé"}
        require(uri.userInfo==null){"Identifiants dans l’URL du flux refusés"}
        // Keep path and port as provided by OpenWebif; only translate receiver-local loopback if needed.
        if(host==uri.host)raw else URL(uri.protocol,host,uri.port,uri.file).toString()
    }
}
