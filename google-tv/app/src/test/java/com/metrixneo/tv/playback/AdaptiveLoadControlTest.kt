package com.metrixneo.tv.playback

import androidx.media3.exoplayer.analytics.PlayerId
import org.junit.Assert.*
import org.junit.Test

/** Exercise the real Media3 interface calls used during ExoPlayer construction. */
class AdaptiveLoadControlTest {
    @Test fun playerConstructionCanQueryBackBufferAndAllocator() {
        val control = AdaptiveLoadControl()
        assertEquals(0L, control.getBackBufferDurationUs(PlayerId.UNSET))
        assertFalse(control.retainBackBufferFromKeyframe(PlayerId.UNSET))
        assertSame(control.getAllocator(), control.getAllocator())
    }
    @Test fun bothPoliciesAcceptPlayerLifecycleAndRepeatedPrepare() {
        val control = AdaptiveLoadControl()
        val id = PlayerId.UNSET
        control.onPrepared(id)
        control.onStopped(id)
        control.onPrepared(id)
        control.onReleased(id)
    }
}
