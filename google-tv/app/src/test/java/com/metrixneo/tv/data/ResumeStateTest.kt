package com.metrixneo.tv.data

import org.junit.Assert.*
import org.junit.Test

class ResumeStateTest {
    @Test fun nestedBouquetAndSeparatePlayingSourceSurviveRoundTrip() {
        val folder = ResumeSource("folder", "France", "folder-fr", listOf(ResumeFolder("Bouquets TV", null, 4), ResumeFolder("Provider", "folder-provider", 2)))
        val state = ResumeState(folder, "service-selected", 27, "channels", Channel("Last played", "1:0:1:123:0:0:0:0:0:0:", "Italy"), ResumeSource("bouquet", "Italy"))
        assertEquals(state, ResumeState.decode(state.encode()))
    }
    @Test fun allServicesAndBrowsingWithoutPlaybackArePreserved() {
        val state = ResumeState(ResumeSource("all"), "selected", 10435, "channels", null, null)
        assertEquals(state, ResumeState.decode(state.encode()))
    }
    @Test fun movedChannelIsSelectedByReferenceInsteadOfOldNumber() {
        assertEquals(2, restoredIndex(listOf("c", "a", "b"), "b", 0))
    }
    @Test fun removedChannelBoundsFallbackAndEmptyListsStaySafe() {
        assertEquals(1, restoredIndex(listOf("a", "b"), "removed", 40))
        assertEquals(0, restoredIndex(emptyList(), "removed", 40))
        assertEquals(0, restoredIndex(listOf("a"), null, -4))
    }
    @Test fun unknownSchemaAndOversizedBookmarksAreRejected() {
        val text = ResumeState(ResumeSource("all"), null, 0, "channels", null, null).encode()
        assertNull(ResumeState.decode(text.replace("\"version\":1", "\"version\":99")))
        assertNull(ResumeState.decode("x".repeat(131073)))
    }
    @Test fun receiverDirectoryCannotBeRestoredAsAPlayingChannel() {
        val state = ResumeState(ResumeSource("all"), null, 0, "player", Channel("Folder", "1:7:1:0:0:0:0:0:0:0:"), ResumeSource("all"))
        assertNull(ResumeState.decode(state.encode()))
    }
}
