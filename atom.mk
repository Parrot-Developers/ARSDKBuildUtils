LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)

LOCAL_CATEGORY_PATH := dragon/libs
LOCAL_MODULE := ARSDKBuildUtils
LOCAL_DESCRIPTION := ARSDK Build Utils

LOCAL_COPY_TO_BUILD_DIR := 1

include $(BUILD_CUSTOM)

