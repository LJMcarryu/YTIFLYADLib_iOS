# 版本记录

## [6.5.0] - 更新说明

> `6.5.0` 已验证 CocoaPods、SwiftPM 的安装、版本锁定与模拟器构建；真机广告展示需在宿主 App 中联调。

<!-- ifly-release-status: {"version":"6.5.0","status":"FAST_UNVERIFIED","distribution":"tos","releaseUrl":"https://download-adsdk.voiceads.cn/ios_sdk/6.5.0/yt/fast-release-record.json"} -->

> 以下为历史版本记录，验收结论仅适用于各节明确列出的历史版本。

## [6.4.6] - TOS 分发

调整 SDK 下载分发，安装入口保持不变。

下载文件与校验值见[版本下载记录](https://download-adsdk.voiceads.cn/ios_sdk/6.4.6/yt/release-record.json)。


## [6.4.4] - 发布工程优化

<a id="变更"></a>

优化 SDK 分发。公开 API、广告形式和最低系统要求保持不变。


## [6.4.2] - 冻结与发布记录

更新 SDK 分发。


## 6.4.1 - 发布工程优化

<a id="变更-1"></a>
<a id="变更-2"></a>

优化 SDK 分发。


## 6.4.0 冻结与发布记录

<a id="变更-3"></a>

优化多窗口场景下的广告展示与页面返回。

开屏 `customWindow` 须与宿主页面处于同一 Scene，并保持可见、尺寸有效。


## 6.3.5

优化广告加载、展示及视频播放。


## 6.3.1（2026-09-01）

优化广告加载与诊断信息。


## 6.3.0（2026-08-25）

更新 SDK，继续支持开屏、插屏及图片和视频素材。


## 6.2.4（2026-08-17）

更新版本分发。


## 6.2.3

首次提供 YT 独立 SDK，支持开屏、插屏及图片和视频素材，最低支持 iOS 11.0。

提供 CocoaPods、SwiftPM 与手动接入；模块名为 `YTIFLYADLib`，类型和方法分别使用 `YTIFLY*`、`ytifly_*` 前缀。
