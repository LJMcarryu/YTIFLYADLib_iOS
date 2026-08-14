# 版本记录

## 6.2.3

- `releaseState`：`FORMAL`
- `binarySourceCommit`（SDK 二进制源码提交）：`c90c8e969b05d4d55b522cb162ab0f2e37aacc52`
- `releaseMetadataCommit`（仅回填 checksum、扫描汇总和发布验收事实，不是 SDK 二进制源码提交）：`b340fe7cccc27af37fc6223042f9638e507a4b63`
- `releaseState=FORMAL` 表示正式签名资产、checksum 和 A/B 元数据已经冻结；公开可用性以同版本 GitHub Release 和发布后 CI 为准。

- 首次准备优推（YT）独立公开分发仓。
- framework/module 为 `YTIFLYADLib`，framework Bundle ID 为 `com.gameley.www.YouTuiAdSDK`。
- 类型、方法、资源和日志白标为 `YTIFLY*`、`ytifly_*`、`YTAdvSDK.bundle`、`[YTAd]`。
- Model B 整变体仅保留开屏、插屏和图片/视频素材能力；物理裁剪 Banner、Reward 和 NativeFeed。
- 普通请求固定使用通用地址 `https://msdk.voiceads.cn/sdk/req`，`customAdRequestURL=false`。
- 准备 CocoaPods、SwiftPM 和手动接入产物，正式 Release 资产库存固定为四项。
- 正式签名产物和 checksum 已冻结并完成本地校验；公开可用性以同版本 GitHub Release 和发布后 CI 为准。
