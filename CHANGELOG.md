# 版本记录

## 6.2.4（待发布）

- `releaseState`：`FORMAL`
- `binarySourceCommit`（SDK 二进制源码提交）：`b0f745d582ce2bed5110702cff972be4153e5038`
- `releaseMetadataCommit`（仅回填 checksum、扫描汇总和发布验收事实，不是 SDK 二进制源码提交）：`7b08118b43a0c4441de4c76a64f34fa54b3fe889`
- `candidateId`：`61f427469346615982e0225fad8187611794cc0a54c452da83073e89fd5ea1bd`
- `YTIFLYADLib.xcframework.zip` 的 SwiftPM checksum/SHA-256：`5f3df44ec856f9e38c584311512ede168cf2c0ec45e3d09378052e1b0196e263`；`YTIFLYADLib-6.2.4.zip` 的 SHA-256：`5207fbc790d055af81f6c33d8558ce3d1e834875e3cd283cb4ccb8dc34d35de9`。
- `releaseState=FORMAL` 表示正式签名资产、checksum 和 A/B 元数据已经冻结；`delivery-manifest.json` 同步绑定提交 A。GitHub Tag/Release、无 Token 匿名下载和正式消费验证仍待编排器完成。
- 公开可用性以同版本 GitHub Release 和发布后 CI 为准。
- `release-state.json` 在 `main` 继续保留历史 `6.2.3/CLOSED`；编排器生成的候选必须是 `6.2.4/FROZEN`。
- YT 不包含 NativeFeed，本版不引入外部 CTA 或 `71503` 行为变化；仍从统一提交 A 重建，以保持四渠道版本一致并带出发布控制面改进。
- 本版继续只包含 Splash、Interstitial 与图片/视频能力，白标、Bundle ID、资源、日志和通用请求地址契约不变。
- Apple Review 扫描未执行且不是发布门禁：`requiredForRelease=false`、`statusAtFreeze=not-run`、`evidenceIncluded=false`；未扫描不得表述为通过。

## 6.2.3

- `releaseState`：`FORMAL`
- `binarySourceCommit`（SDK 二进制源码提交）：`ea0240e620b57d7275e486199099c648f51de257`
- `releaseMetadataCommit`（仅回填 checksum、扫描汇总和发布验收事实，不是 SDK 二进制源码提交）：`0f26b7647e6c1aadb32eca68b24f6845639a59c2`
- `releaseState=FORMAL` 表示正式签名资产、checksum 和 A/B 元数据已经冻结。
- 公开可用性以同版本 GitHub Release 和发布后 CI 为准。

- 首次发布优推（YT）独立公开分发仓。
- framework/module 为 `YTIFLYADLib`，framework Bundle ID 为 `com.gameley.www.YouTuiAdSDK`。
- 类型、方法、资源和日志白标为 `YTIFLY*`、`ytifly_*`、`YTAdvSDK.bundle`、`[YTAd]`。
- Model B 整变体仅保留开屏、插屏和图片/视频素材能力；物理裁剪 Banner、Reward 和 NativeFeed。
- 普通请求固定使用通用地址 `https://msdk.voiceads.cn/sdk/req`，`customAdRequestURL=false`。
- 提供 CocoaPods、SwiftPM 和手动接入产物，正式 Release 资产库存固定为四项。
- 正式签名产物和 checksum 已冻结并公开；`YTIFLYADLib-6.2.3.zip` 的 SHA-256 为 `64e168120aac5f412ab96bdef78fff14e7ba75aae234a08d737fa5ad21c3e537`。[GitHub Release 6.2.3](https://github.com/LJMcarryu/YTIFLYADLib_iOS/releases/tag/6.2.3) 的 annotated tag 解引用到 `09148ce3c651b3dfc35cae3c873baab6d8105950`，4 个资产已通过无 Token 匿名验证与正式消费 [Run 31941599341](https://github.com/LJMcarryu/YTIFLYADLib_iOS/actions/runs/31941599341)。
- 本版本未执行主动 Apple Review 扫描，该扫描不属于发布门禁；冻结状态为 `requiredForRelease=false`、`statusAtFreeze=not-run`、`evidenceIncluded=false`，不得表述为通过。
