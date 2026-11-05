package com.metrixneo.tv.data

import org.json.JSONArray
import org.json.JSONObject

internal data class ResumeFolder(val title: String, val ref: String?, val index: Int)
internal data class ResumeSource(val kind: String, val name: String = "", val ref: String? = null, val parents: List<ResumeFolder> = emptyList())
internal data class ResumeState(
    val source: ResumeSource, val selectedRef: String?, val index: Int, val page: String,
    val playing: Channel?, val playingSource: ResumeSource?
) {
    fun encode(): String {
        fun source(value: ResumeSource): JSONObject = JSONObject().put("kind", value.kind).put("name", value.name)
            .put("ref", value.ref ?: JSONObject.NULL).put("parents", JSONArray().apply {
                value.parents.takeLast(16).forEach { put(JSONObject().put("title", it.title).put("ref", it.ref ?: JSONObject.NULL).put("index", it.index)) }
            })
        return JSONObject().put("version", 1).put("source", source(this.source))
            .put("selected", selectedRef ?: JSONObject.NULL).put("index", index).put("page", page)
            .put("playing", playing?.let { JSONObject().put("name", it.name).put("ref", it.ref).put("bouquet", it.bouquet) } ?: JSONObject.NULL)
            .put("playingSource", playingSource?.let { source(it) } ?: JSONObject.NULL).toString()
    }

    companion object {
        fun decode(text: String): ResumeState? = try {
            require(text.length <= 131072)
            val data = JSONObject(text); require(data.getInt("version") == 1)
            fun optional(o: JSONObject, key: String): String? = if (o.isNull(key)) null else o.getString(key).also { require(it.length <= 16384) }
            fun source(o: JSONObject): ResumeSource {
                val kind = o.getString("kind"); require(kind in setOf("all", "bouquet", "folder", "satellite"))
                val name = o.getString("name"); require(name.length <= 512)
                val ref = optional(o, "ref")
                require(kind != "satellite" || !ref.isNullOrBlank())
                require(kind != "bouquet" || name.isNotBlank())
                val parents = o.getJSONArray("parents"); require(parents.length() <= 16)
                return ResumeSource(kind, name, ref, (0 until parents.length()).map { i ->
                    val f = parents.getJSONObject(i)
                    ResumeFolder(f.getString("title").also { require(it.length <= 512) }, optional(f, "ref"), f.getInt("index").coerceAtLeast(0))
                })
            }
            val playing = data.optJSONObject("playing")?.let { Channel(it.getString("name"), it.getString("ref"), it.getString("bouquet")) }
            require(playing == null || (playing.name.length <= 512 && playing.ref.length in 1..16384 && !isDirectoryRef(playing.ref)))
            val page = data.getString("page"); require(page in setOf("channels", "player", "folders"))
            ResumeState(source(data.getJSONObject("source")), optional(data, "selected"), data.getInt("index").coerceAtLeast(0), page,
                playing, data.optJSONObject("playingSource")?.let { source(it) })
        } catch (_: Exception) { null }
    }
}

/** Prefer stable service identity if the receiver reordered its list; otherwise bound the old cursor. */
internal fun restoredIndex(refs: List<String>, selectedRef: String?, fallback: Int): Int =
    refs.indexOf(selectedRef).takeIf { it >= 0 } ?: fallback.coerceIn(0, refs.lastIndex.coerceAtLeast(0))
