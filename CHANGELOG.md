# 版本记录

## 6.3.1（2026-09-01）

<!-- ifly-release-status: {"schemaVersion":1,"version":"6.3.1","releaseState":"FORMAL","distribution":"github-release","releaseUrl":"https://github.com/LJMcarryu/YTIFLYADLib_iOS/releases/tag/6.3.1"} -->

- `releaseState`：`FORMAL`
- `binarySourceCommit`（SDK 二进制源码提交）：`b7e46a9f06897924d3d69d4d6a7e43f6237d8579`
- `releaseMetadataCommit`（仅回填 checksum、扫描汇总和发布验收事实，不是 SDK 二进制源码提交）：`b86f5d7dc5e1105194889bc60a5ee9eec40b611f`
- `candidateId`：`74f506ec2562caac2d0f1f48a404c1c3b69a1a2d29463ce94067b18821d1f1d7`
- `YTIFLYADLib.xcframework.zip` 的 SwiftPM checksum/SHA-256：`7adf06f9c3f1d6fe915679322ccb941ba9122edf496c9815db12db3f4e459855`；`YTIFLYADLib-6.3.1.zip` 的 SHA-256：`c47eb332cc58c864b49b3a17f594debf80f4259a9b8123b7b437ff1657fe6f1f`；`checksums.txt` 的 SHA-256：`2a42ddd0da3656729e486e90e81bcd39c7a631a4432778e1fd50ae52d41c5c2f`。
- `releaseState=FORMAL` 表示正式签名资产、checksum 和 A/B 元数据已经冻结；`delivery-manifest.json` 同步绑定提交 A。
- YT 不包含 NativeFeed 和 Banner；本版从统一提交 A 重建，仅同步共享 Core 诊断与安全网，不新增被裁剪格式的公开能力。
- Apple Review 扫描未执行且不是发布门禁：`requiredForRelease=false`、`statusAtFreeze=not-run`、`evidenceIncluded=false`；未扫描不得表述为通过。

## 6.3.0（2026-08-25）

- `releaseState`：`FORMAL`
- `binarySourceCommit`（SDK 二进制源码提交）：`38eb0715f889fe2d585641891923511c9cc3e43e`
- `releaseMetadataCommit`（仅回填 checksum、扫描汇总和发布验收事实，不是 SDK 二进制源码提交）：`0e667f9f1a2d615d3f7e15a552f093c903ff1a57`
- `candidateId`：`1b69dab08ac31e756b707d824b2548c2c2cfd66b343007d00e43efdbee795c44`
- `YTIFLYADLib.xcframework.zip` 的 SwiftPM checksum/SHA-256：`144d0c649c1a83d8572e4a3a1295ec0430a65b788554fe62cccf6c12631a0aa5`；`YTIFLYADLib-6.3.0.zip` 的 SHA-256：`e422b4b7ed238136e90b596e4958bbabf59649dd656e38f394248b7efdb638f6`。
- `releaseState=FORMAL` 表示正式签名资产、checksum 和 A/B 元数据已经冻结；`delivery-manifest.json` 同步绑定提交 A。
- 公开可用性以同版本 GitHub Release 和发布后 CI 为准。
- `release-state.json` 在 `main` 继续保留历史 `6.2.4/CLOSED`；编排器生成的候选必须是 `6.3.0/FROZEN`。
- YT 不包含 NativeFeed，本版不引入外部 CTA、媒体交互优先或结构化 `71503` 行为变化；仍从统一提交 A 重建。
- 本版继续只包含 Splash、Interstitial 与图片/视频能力，白标、Bundle ID、资源、日志和通用请求地址契约不变。
- Apple Review 扫描未执行且不是发布门禁：`requiredForRelease=false`、`statusAtFreeze=not-run`、`evidenceIncluded=false`；未扫描不得表述为通过。

## 6.2.4（2026-08-17）

- `releaseState`：`FORMAL`
- `binarySourceCommit`：`b0f745d582ce2bed5110702cff972be4153e5038`
- `releaseMetadataCommit`：`7b08118b43a0c4441de4c76a64f34fa54b3fe889`
- `candidateId`：`61f427469346615982e0225fad8187611794cc0a54c452da83073e89fd5ea1bd`
- `YTIFLYADLib.xcframework.zip` 的 SHA-256 为 `5f3df44ec856f9e38c584311512ede168cf2c0ec45e3d09378052e1b0196e263`；`YTIFLYADLib-6.2.4.zip` 的 SHA-256 为 `5207fbc790d055af81f6c33d8558ce3d1e834875e3cd283cb4ccb8dc34d35de9`。
- [GitHub Release 6.2.4](https://github.com/LJMcarryu/YTIFLYADLib_iOS/releases/tag/6.2.4) 的 4 个资产已完成无 Token 匿名校验，正式消费 [Run 32027223281](https://github.com/LJMcarryu/YTIFLYADLib_iOS/actions/runs/32027223281) 为 `success`。

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
