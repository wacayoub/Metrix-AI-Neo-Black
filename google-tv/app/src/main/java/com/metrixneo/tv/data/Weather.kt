package com.metrixneo.tv.data

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.net.URL
import java.net.HttpURLConnection
import java.net.URLEncoder

data class WeatherDay(val date: String, val min: Int, val max: Int, val code: Int)
data class WeatherLocation(val city: String, val latitude: Double, val longitude: Double)
data class WeatherInfo(val city: String, val temperature: Int, val code: Int, val isDay: Boolean, val days: List<WeatherDay>, val fetched: Long)
object Weather {
    private fun json(url: String): JSONObject {
        val c = URL(url).openConnection() as HttpURLConnection
        c.connectTimeout = 6000; c.readTimeout = 6000
        try { check(c.responseCode == 200); return c.inputStream.bufferedReader().use { JSONObject(it.readText()) } }
        finally { c.disconnect() }
    }
    suspend fun fetch(city: String, latitude: Double? = null, longitude: Double? = null): WeatherInfo = withContext(Dispatchers.IO) {
        val location = if (latitude != null && longitude != null) JSONObject().put("name", city).put("latitude", latitude).put("longitude", longitude) else {
        val locations = json("https://geocoding-api.open-meteo.com/v1/search?name=" + URLEncoder.encode(city, "UTF-8") + "&count=5&language=fr").optJSONArray("results") ?: error("Ville introuvable")
        check(locations.length() > 0) { "Ville introuvable" }
        (0 until locations.length()).map { locations.getJSONObject(it) }.firstOrNull { city.equals("Casablanca", true) && it.optString("country_code") == "MA" } ?: locations.getJSONObject(0)
        }
        val data = json("https://api.open-meteo.com/v1/forecast?latitude=${location.getDouble("latitude")}&longitude=${location.getDouble("longitude")}&current=temperature_2m,weather_code,is_day&daily=weather_code,temperature_2m_max,temperature_2m_min&forecast_days=4&timezone=auto")
        val c = data.getJSONObject("current"); val d = data.getJSONObject("daily")
        WeatherInfo(location.getString("name"), c.getDouble("temperature_2m").toInt(), c.getInt("weather_code"), c.optInt("is_day", 1) == 1,
            (1..3).map { i -> WeatherDay(d.getJSONArray("time").getString(i), d.getJSONArray("temperature_2m_min").getDouble(i).toInt(), d.getJSONArray("temperature_2m_max").getDouble(i).toInt(), d.getJSONArray("weather_code").getInt(i)) }, System.currentTimeMillis())
    }
    fun icon(code: Int, day: Boolean = true): String = when {
        code == 0 -> if (day) "☀" else "☾"
        code <= 3 -> "☁"
        code in 71..77 || code in 85..86 -> "❄"
        code >= 95 -> "ϟ"
        code in 45..48 -> "≋"
        else -> "☂"
    }
}
