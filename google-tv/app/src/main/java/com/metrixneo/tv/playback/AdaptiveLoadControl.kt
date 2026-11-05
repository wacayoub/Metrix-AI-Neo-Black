package com.metrixneo.tv.playback

import android.util.Log
import androidx.media3.common.C
import androidx.media3.common.Timeline
import androidx.media3.exoplayer.DefaultLoadControl
import androidx.media3.exoplayer.LoadControl
import androidx.media3.exoplayer.analytics.PlayerId
import androidx.media3.exoplayer.source.TrackGroupArray
import androidx.media3.exoplayer.source.MediaSource
import androidx.media3.exoplayer.trackselection.ExoTrackSelection
import androidx.media3.exoplayer.upstream.DefaultAllocator

/** Choose buffering from the selected stream formats, never from a channel's marketing name. */
@androidx.annotation.OptIn(androidx.media3.common.util.UnstableApi::class)
class AdaptiveLoadControl private constructor(private val controls: Controls) : LoadControl {
    constructor() : this(createControls())
    private var highBandwidth = false
    private val active get() = if (highBandwidth) controls.stable else controls.fast
    override fun getAllocator() = controls.fast.allocator
    override fun getBackBufferDurationUs(playerId: PlayerId) = controls.fast.getBackBufferDurationUs(playerId)
    override fun retainBackBufferFromKeyframe(playerId: PlayerId) = controls.fast.retainBackBufferFromKeyframe(playerId)
    override fun shouldContinuePreloading(timeline: Timeline, mediaPeriodId: MediaSource.MediaPeriodId, bufferedDurationUs: Long) =
        active.shouldContinuePreloading(timeline, mediaPeriodId, bufferedDurationUs)

    override fun onPrepared(playerId: PlayerId) {
        highBandwidth = false
        controls.fast.onPrepared(playerId)
        controls.stable.onPrepared(playerId)
    }

    override fun onTracksSelected(parameters: LoadControl.Parameters, trackGroups: TrackGroupArray,
        trackSelections: Array<out ExoTrackSelection?>) {
        highBandwidth = trackSelections.any { selection ->
            selection != null && (0 until selection.length()).any { index ->
                val format = selection.getFormat(index)
                format.height >= 2160 || format.colorInfo?.colorTransfer in listOf(C.COLOR_TRANSFER_ST2084, C.COLOR_TRANSFER_HLG)
            }
        }
        controls.fast.onTracksSelected(parameters, trackGroups, trackSelections)
        controls.stable.onTracksSelected(parameters, trackGroups, trackSelections)
        Log.i("NeoBuffer", if (highBandwidth) "profile=4k_hdr start_ms=4000 rebuffer_ms=6000 max_ms=35000" else "profile=normal start_ms=500 rebuffer_ms=1500 max_ms=12000")
    }

    override fun shouldContinueLoading(parameters: LoadControl.Parameters) = active.shouldContinueLoading(parameters)
    override fun shouldStartPlayback(parameters: LoadControl.Parameters) = active.shouldStartPlayback(parameters)
    override fun onStopped(playerId: PlayerId) {
        controls.fast.onStopped(playerId)
        controls.stable.onStopped(playerId)
    }
    override fun onReleased(playerId: PlayerId) {
        controls.fast.onReleased(playerId)
        controls.stable.onReleased(playerId)
    }

    private data class Controls(val fast: DefaultLoadControl, val stable: DefaultLoadControl)
    companion object {
        private fun createControls(): Controls {
            // Both policies control the same player/allocator, with identical track byte targets.
            val allocator = DefaultAllocator(true, C.DEFAULT_BUFFER_SEGMENT_SIZE)
            fun policy(min: Int, max: Int, start: Int, resume: Int) = DefaultLoadControl.Builder()
                .setAllocator(allocator).setBufferDurationsMs(min, max, start, resume)
                .setPrioritizeTimeOverSizeThresholds(true).build()
            return Controls(policy(3500, 12000, 500, 1500), policy(12000, 35000, 4000, 6000))
        }
    }
}
