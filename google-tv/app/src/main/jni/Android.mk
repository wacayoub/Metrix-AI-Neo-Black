LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)
LOCAL_MODULE := neo_gst
LOCAL_SRC_FILES := neo_gst.c
LOCAL_SHARED_LIBRARIES := gstreamer_android
LOCAL_LDLIBS := -llog -landroid
include $(BUILD_SHARED_LIBRARY)

ifndef GSTREAMER_ROOT_ANDROID
$(error Set GSTREAMER_ROOT_ANDROID to the extracted official GStreamer Android SDK)
endif
ifeq ($(TARGET_ARCH_ABI),armeabi-v7a)
GSTREAMER_ROOT := $(GSTREAMER_ROOT_ANDROID)/armv7
else ifeq ($(TARGET_ARCH_ABI),arm64-v8a)
GSTREAMER_ROOT := $(GSTREAMER_ROOT_ANDROID)/arm64
else
$(error Unsupported GStreamer ABI $(TARGET_ARCH_ABI))
endif
GSTREAMER_NDK_BUILD_PATH := $(GSTREAMER_ROOT)/share/gst-android/ndk-build
include $(GSTREAMER_NDK_BUILD_PATH)/plugins.mk
GSTREAMER_PLUGINS := coreelements typefindfunctions playback autodetect opengl opensles androidmedia \
    audioconvert audioresample audioparsers videoconvertscale videoparsersbad mpegtsdemux isomp4 matroska \
    soup tcp udp rtp rtpmanager rtsp hls adaptivedemux2 libav subparse pango
GSTREAMER_EXTRA_DEPS := gstreamer-video-1.0 gstreamer-audio-1.0
G_IO_MODULES := openssl
# AGP requires an absolute prebuilt output path in ndk-build's model.
override GSTREAMER_BUILD_DIR := $(abspath $(NDK_OUT))/gst-android-build/$(TARGET_ARCH_ABI)
include $(GSTREAMER_NDK_BUILD_PATH)/gstreamer-1.0.mk
