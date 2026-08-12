# 版本记录

## 6.2.3（待发布）

- `releaseState`：`PENDING`
- `binarySourceCommit`（SDK 二进制源码提交）：`__YTIFLYADLIB_6_2_3_BINARY_SOURCE_COMMIT_PENDING__`
- `releaseMetadataCommit`（仅回填 checksum、扫描汇总和发布验收事实，不是 SDK 二进制源码提交）：`__YTIFLYADLIB_6_2_3_RELEASE_METADATA_COMMIT_PENDING__`

- 首次准备优推（YT）独立公开分发仓。
- framework/module 为 `YTIFLYADLib`，framework Bundle ID 为 `com.gameley.www.YouTuiAdSDK`。
- 类型、方法、资源和日志白标为 `YTIFLY*`、`ytifly_*`、`YTAdvSDK.bundle`、`[YTAd]`。
- Model B 整变体仅保留开屏、插屏和图片/视频素材能力；物理裁剪 Banner、Reward 和 NativeFeed。
- 普通请求固定使用通用地址 `https://msdk.voiceads.cn/sdk/req`，`customAdRequestURL=false`。
- 准备 CocoaPods、SwiftPM 和手动接入产物，正式 Release 资产库存固定为四项。
- 当前仅为准备态；正式签名产物、checksum、tag 和 Release 尚未生成。
