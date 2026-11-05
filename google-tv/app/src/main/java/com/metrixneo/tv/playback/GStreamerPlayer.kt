package com.metrixneo.tv.playback

import android.content.Context
import android.os.Handler
import android.os.HandlerThread
import android.os.Looper
import android.view.Surface
import android.view.SurfaceHolder
import android.view.SurfaceView
import org.freedesktop.gstreamer.GStreamer

/** All JNI operations run on one worker, including pipeline teardown during zapping. */
class GStreamerPlayer(private val context: Context, private val event: (Int, Long, String, Int, Int) -> Unit) {
    private val thread = HandlerThread("NeoGStreamer").apply { start() }
    private val worker = Handler(thread.looper)
    private val main = Handler(Looper.getMainLooper())
    private var handle = 0L
    @Volatile private var closed = false
    private var sequence = 0L
    @Volatile private var wantedSequence = -1L
    private val poll = object : Runnable {
        override fun run() {
            if (!closed && handle != 0L) nativePoll(handle)
            if (!closed) worker.postDelayed(this, 100)
        }
    }

    init {
        worker.post {
            try {
                System.loadLibrary("gstreamer_android")
                GStreamer.init(context.applicationContext)
                System.loadLibrary("neo_gst")
                handle = nativeCreate()
                check(handle != 0L)
                android.util.Log.i("NeoGst", "init_ready")
            } catch (error: Throwable) {
                android.util.Log.i("NeoGst", "init_error type=${error.javaClass.simpleName}")
                onNativeEvent(4, sequence, "Initialisation de GStreamer impossible sur cet appareil.", 0, 0)
            }
            worker.post(poll)
        }
    }

    fun view(): SurfaceView = SurfaceView(context).apply {
        isFocusable = false
        if (android.os.Build.VERSION.SDK_INT >= 34) setSurfaceLifecycle(SurfaceView.SURFACE_LIFECYCLE_FOLLOWS_ATTACHMENT)
        holder.addCallback(object : SurfaceHolder.Callback {
            override fun surfaceCreated(holder: SurfaceHolder) = surface(holder.surface)
            override fun surfaceChanged(holder: SurfaceHolder, format: Int, width: Int, height: Int) = surface(holder.surface)
            override fun surfaceDestroyed(holder: SurfaceHolder) = surface(null)
        })
    }
    private fun surface(surface: Surface?) { worker.post { if (!closed && handle != 0L) nativeSurface(handle, surface) } }
    fun open(url: String, username: String, password: String, id: Long) {
        wantedSequence = id
        worker.post {
            if (!closed && id == wantedSequence) {
                sequence = id
                if (handle != 0L) nativeOpen(handle, url, username, password, id)
                else onNativeEvent(4, id, "GStreamer indisponible. Choisis Media3 dans Setup.", 0, 0)
            }
        }
    }
    fun pause() { worker.post { if (!closed && handle != 0L) nativePause(handle, true) } }
    fun play() { worker.post { if (!closed && handle != 0L) nativePause(handle, false) } }
    fun stop() { wantedSequence = -1; worker.post { if (!closed && handle != 0L) nativeStop(handle) } }
    fun selectTrack(type: Int, index: Int) { worker.post { if (!closed && handle != 0L) nativeTrack(handle, type, index) } }
    fun release() {
        worker.post {
            closed = true
            worker.removeCallbacks(poll)
            if (handle != 0L) nativeRelease(handle)
            handle = 0L
            thread.quitSafely()
        }
    }
    // The native layer emits fixed messages/codes, never stream URLs or provider tokens.
    @Suppress("unused")
    private fun onNativeEvent(kind: Int, id: Long, detail: String, width: Int, height: Int) {
        main.post { if (!closed) event(kind, id, detail, width, height) }
    }
    private external fun nativeCreate(): Long
    private external fun nativeOpen(handle: Long, url: String, username: String, password: String, id: Long)
    private external fun nativeSurface(handle: Long, surface: Surface?)
    private external fun nativePoll(handle: Long)
    private external fun nativePause(handle: Long, paused: Boolean)
    private external fun nativeStop(handle: Long)
    private external fun nativeTrack(handle: Long, type: Int, index: Int)
    private external fun nativeRelease(handle: Long)
}
