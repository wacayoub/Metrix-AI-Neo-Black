#include <jni.h>
#include <android/native_window_jni.h>
#include <android/log.h>
#include <gst/gst.h>
#include <gst/video/videooverlay.h>

typedef struct {
    GstElement *pipeline, *video;
    GstBus *bus;
    GstStreamCollection *streams;
    ANativeWindow *window;
    gchar *username, *password;
    jlong sequence;
    gboolean desired_playing, buffering, started, metadata;
    gint frame;
    gint width, height, audio_tracks, text_tracks;
    gint audio_selected, text_selected;
    GstState reported_state;
    GMutex window_lock;
} NeoPlayer;

#define PTR(h) ((NeoPlayer *)(guintptr)(h))
#define JNI(name) Java_com_metrixneo_tv_playback_GStreamerPlayer_##name

static void emit(JNIEnv *env, jobject self, NeoPlayer *p, gint kind, const gchar *detail, gint w, gint h) {
    jclass cls = (*env)->GetObjectClass(env, self);
    jmethodID method = (*env)->GetMethodID(env, cls, "onNativeEvent", "(IJLjava/lang/String;II)V");
    jstring value = (*env)->NewStringUTF(env, detail ? detail : "");
    (*env)->CallVoidMethod(env, self, method, kind, p->sequence, value, w, h);
    (*env)->DeleteLocalRef(env, value);
    (*env)->DeleteLocalRef(env, cls);
}

static gboolean drawn(GstElement *sink, gpointer context, GstSample *sample, gpointer user) {
    NeoPlayer *p = user;
    GstCaps *caps = sample ? gst_sample_get_caps(sample) : NULL;
    if (caps && !gst_caps_is_empty(caps)) {
        const GstStructure *s = gst_caps_get_structure(caps, 0);
        gint width = 0, height = 0;
        gst_structure_get_int(s, "width", &width); gst_structure_get_int(s, "height", &height);
        g_atomic_int_set(&p->width, width); g_atomic_int_set(&p->height, height);
    }
    g_atomic_int_set(&p->frame, 1);
    return FALSE; /* Let glimagesink perform its normal drawing. */
}

/* A same-state request need not generate a bus message. Publish only the actual state. */
static void report_state(JNIEnv *env, jobject self, NeoPlayer *p) {
    GstState state, pending;
    if (gst_element_get_state(p->pipeline, &state, &pending, 0) == GST_STATE_CHANGE_FAILURE) return;
    if (state == p->reported_state) return;
    p->reported_state = state;
    __android_log_print(ANDROID_LOG_INFO, "NeoGstNative", "state id=%lld actual=%d pending=%d wanted=%d",
        (long long)p->sequence, state, pending, p->desired_playing);
    if (state == GST_STATE_PLAYING && p->desired_playing) emit(env, self, p, 2, "", 0, 0);
    else if (state == GST_STATE_PAUSED && !p->desired_playing) emit(env, self, p, 8, "", 0, 0);
}

static GstBusSyncReply sync_message(GstBus *bus, GstMessage *msg, gpointer user) {
    NeoPlayer *p = user;
    if (gst_is_video_overlay_prepare_window_handle_message(msg)) {
        g_mutex_lock(&p->window_lock);
        if (p->window) gst_video_overlay_set_window_handle(GST_VIDEO_OVERLAY(GST_MESSAGE_SRC(msg)), (guintptr)p->window);
        g_mutex_unlock(&p->window_lock);
        gst_message_unref(msg);
        return GST_BUS_DROP;
    }
    return GST_BUS_PASS;
}

static void source_setup(GstElement *pipeline, GstElement *source, gpointer user) {
    NeoPlayer *p = user;
    GObjectClass *cls = G_OBJECT_GET_CLASS(source);
    if (g_object_class_find_property(cls, "timeout")) g_object_set(source, "timeout", 15u, NULL);
    if (g_object_class_find_property(cls, "http-log-level")) g_object_set(source, "http-log-level", 0, NULL);
    if (p->username && *p->username && g_object_class_find_property(cls, "user-id")) {
        if (g_object_class_find_property(cls, "automatic-redirect")) g_object_set(source, "automatic-redirect", FALSE, NULL);
        g_object_set(source, "user-id", p->username, "user-pw", p->password, NULL);
    }
}

JNIEXPORT jlong JNICALL JNI(nativeCreate)(JNIEnv *env, jobject self) {
    gst_debug_set_default_threshold(GST_LEVEL_NONE);
    NeoPlayer *p = g_new0(NeoPlayer, 1);
    g_mutex_init(&p->window_lock);
    p->pipeline = gst_element_factory_make("playbin3", NULL);
    p->video = gst_element_factory_make("glimagesink", NULL);
    GstElement *audio = gst_element_factory_make("openslessink", NULL);
    if (!p->pipeline || !p->video || !audio) {
        if (p->pipeline) gst_object_unref(p->pipeline);
        if (p->video) gst_object_unref(p->video);
        if (audio) gst_object_unref(audio);
        g_mutex_clear(&p->window_lock); g_free(p); return 0;
    }
    gst_object_ref_sink(p->video);
    gst_object_ref_sink(audio);
    /* Keep sink preroll from holding the live pipeline's control transitions. */
    g_object_set(p->video, "async", FALSE, NULL);
    g_object_set(audio, "async", FALSE, NULL);
    g_object_set(p->pipeline, "video-sink", p->video, "audio-sink", audio,
        "buffer-duration", (gint64)(1500 * GST_MSECOND), NULL);
    gst_object_unref(audio);
    g_signal_connect(p->video, "client-draw", G_CALLBACK(drawn), p);
    g_signal_connect(p->pipeline, "source-setup", G_CALLBACK(source_setup), p);
    p->bus = gst_element_get_bus(p->pipeline);
    gst_bus_set_sync_handler(p->bus, sync_message, p, NULL);
    return (jlong)(guintptr)p;
}

static void stop(NeoPlayer *p) {
    p->desired_playing = FALSE;
    gst_element_set_state(p->pipeline, GST_STATE_NULL);
    gst_bus_set_flushing(p->bus, TRUE);
    gst_bus_set_flushing(p->bus, FALSE);
    p->started = FALSE; p->metadata = FALSE; p->buffering = FALSE; g_atomic_int_set(&p->frame, 0);
    p->reported_state = GST_STATE_VOID_PENDING;
    g_atomic_int_set(&p->width, 0); g_atomic_int_set(&p->height, 0);
    p->audio_tracks = 0; p->text_tracks = 0;
    p->audio_selected = 0; p->text_selected = -1;
    gst_clear_object(&p->streams);
}

JNIEXPORT void JNICALL JNI(nativeOpen)(JNIEnv *env, jobject self, jlong handle, jstring url, jstring username, jstring password, jlong seq) {
    NeoPlayer *p = PTR(handle);
    /* READY releases the previous network source/decoder while retaining the video window. */
    p->desired_playing = FALSE;
    gst_element_set_state(p->pipeline, GST_STATE_READY);
    gst_bus_set_flushing(p->bus, TRUE); gst_bus_set_flushing(p->bus, FALSE);
    p->started = FALSE; p->metadata = FALSE; p->buffering = FALSE; g_atomic_int_set(&p->frame, 0);
    p->reported_state = GST_STATE_VOID_PENDING;
    g_atomic_int_set(&p->width, 0); g_atomic_int_set(&p->height, 0);
    p->audio_tracks = 0; p->text_tracks = 0;
    p->audio_selected = 0; p->text_selected = -1;
    gst_clear_object(&p->streams);
    p->sequence = seq;
    const char *u = (*env)->GetStringUTFChars(env, url, NULL);
    const char *name = (*env)->GetStringUTFChars(env, username, NULL);
    const char *pass = (*env)->GetStringUTFChars(env, password, NULL);
    g_free(p->username); g_free(p->password); p->username = g_strdup(name); p->password = g_strdup(pass);
    g_object_set(p->pipeline, "uri", u, NULL);
    guint flags = 0; g_object_get(p->pipeline, "flags", &flags, NULL);
    g_object_set(p->pipeline, "flags", flags & ~4u, NULL);
    (*env)->ReleaseStringUTFChars(env, url, u);
    (*env)->ReleaseStringUTFChars(env, username, name);
    (*env)->ReleaseStringUTFChars(env, password, pass);
    p->desired_playing = TRUE;
    if (p->window) gst_video_overlay_set_window_handle(GST_VIDEO_OVERLAY(p->video), (guintptr)p->window);
    if (p->window) gst_element_set_state(p->pipeline, GST_STATE_PLAYING);
    emit(env, self, p, 3, "Mise en mémoire tampon…", 0, 0);
}

JNIEXPORT void JNICALL JNI(nativeSurface)(JNIEnv *env, jobject self, jlong handle, jobject surface) {
    NeoPlayer *p = PTR(handle);
    ANativeWindow *next = surface ? ANativeWindow_fromSurface(env, surface) : NULL;
    if (next == p->window) {
        if (next) ANativeWindow_release(next);
        return;
    }
    if (p->window) gst_element_set_state(p->pipeline, GST_STATE_READY);
    g_mutex_lock(&p->window_lock);
    gst_video_overlay_set_window_handle(GST_VIDEO_OVERLAY(p->video), (guintptr)next);
    if (p->window) ANativeWindow_release(p->window);
    p->window = next;
    g_mutex_unlock(&p->window_lock);
    if (next && p->desired_playing) gst_element_set_state(p->pipeline, GST_STATE_PLAYING);
}

JNIEXPORT void JNICALL JNI(nativePoll)(JNIEnv *env, jobject self, jlong handle) {
    NeoPlayer *p = PTR(handle); GstMessage *msg;
    /* Integrate default GLib sources with Android's HandlerThread without a blocking loop. */
    for (guint dispatch = 0; dispatch < 8 && g_main_context_pending(NULL); dispatch++)
        g_main_context_iteration(NULL, FALSE);
    /* Yield to queued remote commands even if the source produces a busy bus. */
    for (guint count = 0; count < 64 && (msg = gst_bus_pop(p->bus)); count++) {
        switch (GST_MESSAGE_TYPE(msg)) {
            case GST_MESSAGE_ERROR: {
                GError *error = NULL; gchar *debug = NULL;
                gst_message_parse_error(msg, &error, &debug);
                /* GStreamer error/debug strings may contain provider credentials: never forward them. */
                if (error) __android_log_print(ANDROID_LOG_INFO, "NeoGstNative", "error id=%lld domain=%s code=%d",
                    (long long)p->sequence, g_quark_to_string(error->domain), error->code);
                const char *text = (error && error->domain == GST_RESOURCE_ERROR) ?
                    "GStreamer : accès au flux impossible. Vérifie la connexion et la disponibilité de la chaîne." :
                    "GStreamer : lecture impossible (flux ou codec non pris en charge).";
                emit(env, self, p, 4, text, 0, 0);
                g_clear_error(&error); g_free(debug); p->desired_playing = FALSE;
                gst_element_set_state(p->pipeline, GST_STATE_NULL);
                break;
            }
            case GST_MESSAGE_BUFFERING: {
                gint percent; gst_message_parse_buffering(msg, &percent);
                gboolean buffering = percent < 100;
                if (buffering != p->buffering) {
                    p->buffering = buffering;
                    if (p->desired_playing) {
                        /* TV sources may need PLAYING to supply the data that fills the
                           buffer. Pausing here can leave READY -> PAUSED pending forever. */
                        report_state(env, self, p);
                        if (p->reported_state != GST_STATE_PLAYING && p->buffering)
                            emit(env, self, p, 3, "Mise en mémoire tampon…", 0, 0);
                    }
                }
                break;
            }
            case GST_MESSAGE_STATE_CHANGED:
                if (GST_MESSAGE_SRC(msg) == GST_OBJECT(p->pipeline)) {
                    report_state(env, self, p);
                }
                break;
            case GST_MESSAGE_STREAM_COLLECTION: {
                GstStreamCollection *collection = NULL;
                gst_message_parse_stream_collection(msg, &collection);
                if (collection) {
                    p->audio_tracks = 0; p->text_tracks = 0;
                    for (guint i = 0; i < gst_stream_collection_get_size(collection); i++) {
                        GstStream *stream = gst_stream_collection_get_stream(collection, i);
                        GstStreamType type = gst_stream_get_stream_type(stream);
                        if (type & GST_STREAM_TYPE_AUDIO) p->audio_tracks++;
                        if (type & GST_STREAM_TYPE_TEXT) p->text_tracks++;
                    }
                    p->metadata = FALSE;
                    gst_clear_object(&p->streams);
                    p->streams = collection;
                }
                break;
            }
            case GST_MESSAGE_EOS: emit(env, self, p, 5, "Fin du flux.", 0, 0); break;
            default: break;
        }
        gst_message_unref(msg);
    }
    report_state(env, self, p);
    if ((!p->metadata || !p->started) && p->desired_playing) {
        /* Read event snapshots; querying playbin pads here can block every queued command. */
        gint w = g_atomic_int_get(&p->width), h = g_atomic_int_get(&p->height);
        gint audio = p->audio_tracks, text = p->text_tracks;
        gchar *tracks = g_strdup_printf("%d:%d", audio, text);
        /* Hardware video surfaces may not expose dimensions; audio/text discovery is independent. */
        if (!p->metadata && ((w > 0 && h > 0) || audio > 0 || text > 0)) {
            p->metadata = TRUE;
            emit(env, self, p, 6, tracks, w, h);
        }
        if (!p->started && g_atomic_int_get(&p->frame)) {
            p->started = TRUE;
            emit(env, self, p, 7, tracks, w, h);
        }
        g_free(tracks);
    }
}

JNIEXPORT void JNICALL JNI(nativePause)(JNIEnv *env, jobject self, jlong handle, jboolean paused) {
    NeoPlayer *p = PTR(handle); p->desired_playing = !paused;
    __android_log_print(ANDROID_LOG_INFO, "NeoGstNative", "control id=%lld paused=%d", (long long)p->sequence, paused);
    p->reported_state = GST_STATE_VOID_PENDING;
    GstStateChangeReturn changed = gst_element_set_state(p->pipeline, paused ? GST_STATE_PAUSED : GST_STATE_PLAYING);
    __android_log_print(ANDROID_LOG_INFO, "NeoGstNative", "control_return id=%lld result=%d", (long long)p->sequence, changed);
    report_state(env, self, p);
}
JNIEXPORT void JNICALL JNI(nativeStop)(JNIEnv *env, jobject self, jlong handle) { stop(PTR(handle)); }
JNIEXPORT void JNICALL JNI(nativeTrack)(JNIEnv *env, jobject self, jlong handle, jint type, jint index) {
    NeoPlayer *p = PTR(handle);
    if (!p->streams) return;
    if (type == 1) {
        if (index < 0 || index >= p->audio_tracks) return;
        p->audio_selected = index;
    } else {
        if (index < -1 || index >= p->text_tracks) return;
        p->text_selected = index;
    }
    guint flags = 0; g_object_get(p->pipeline, "flags", &flags, NULL);
    g_object_set(p->pipeline, "flags", p->text_selected < 0 ? (flags & ~4u) : (flags | 4u), NULL);
    /* playbin3 selects stream IDs, rather than playbin2's removed current-* properties. */
    GList *ids = NULL;
    gint audio = 0, text = 0;
    gboolean video = FALSE;
    for (guint i = 0; i < gst_stream_collection_get_size(p->streams); i++) {
        GstStream *stream = gst_stream_collection_get_stream(p->streams, i);
        GstStreamType kind = gst_stream_get_stream_type(stream);
        gboolean include = FALSE;
        if ((kind & GST_STREAM_TYPE_VIDEO) && !video) { include = TRUE; video = TRUE; }
        if (kind & GST_STREAM_TYPE_AUDIO) include = audio++ == p->audio_selected;
        if (kind & GST_STREAM_TYPE_TEXT) include = text++ == p->text_selected;
        const gchar *id = gst_stream_get_stream_id(stream);
        if (include && id) ids = g_list_append(ids, (gpointer)id);
    }
    if (ids) {
        gboolean accepted = gst_element_send_event(p->pipeline, gst_event_new_select_streams(ids));
        __android_log_print(ANDROID_LOG_INFO, "NeoGstNative", "track id=%lld type=%d index=%d accepted=%d",
            (long long)p->sequence, type, index, accepted);
        g_list_free(ids);
    }
}
JNIEXPORT void JNICALL JNI(nativeRelease)(JNIEnv *env, jobject self, jlong handle) {
    NeoPlayer *p = PTR(handle); stop(p);
    gst_bus_set_sync_handler(p->bus, NULL, NULL, NULL);
    gst_object_unref(p->bus); gst_object_unref(p->pipeline); gst_object_unref(p->video);
    if (p->window) ANativeWindow_release(p->window);
    g_free(p->username); g_free(p->password); g_mutex_clear(&p->window_lock); g_free(p);
}
