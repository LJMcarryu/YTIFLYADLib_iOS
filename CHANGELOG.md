# 版本记录

## 6.4.0 候选（待联调）

<!-- ifly-release-candidate: {"schemaVersion":1,"version":"6.4.0","releaseState":"CANDIDATE","publicationState":"UNPUBLISHED","repository":"LJMcarryu/YTIFLYADLib_iOS","currentFormalVersion":"6.3.5"} -->

`6.4.0` 尚未发布，本节仅记录待联调候选行为。当前公开正式版仍为 `6.3.5`；既有 Tag、Release 和资产保持不可变。

### 变更

- 共享 UIScene 适配：展示、落地页、外跳回流、曝光判断和 UI 生命周期使用广告的实际来源 window/Scene；完全没有来源时，只允许唯一且明确的前台应用 Scene，不跨 Scene 随机兜底。独立落地页始终归属来源 Scene。
- 收紧开屏 `customWindow` 的 Scene 宿主验收：rootVC 仍须入窗；`customWindow` 必须可见、尺寸有限且为正、已关联 Scene，并与 `rootVC.window` 同 Scene。合法窗口可以不是 key window，可以使用较高 `windowLevel`，也可以没有 rootVC。
- 无 Scene、跨 Scene、隐藏或尺寸无效的 `customWindow` 会导致展示失败；失败不锁死本次机会，媒体修正后可以重试。
- 公开 API 方法签名不变。

## 6.3.5

<!-- ifly-release-status: {"schemaVersion":1,"version":"6.3.5","releaseState":"FORMAL","distribution":"github-release","releaseUrl":"https://github.com/LJMcarryu/YTIFLYADLib_iOS/releases/tag/6.3.5"} -->

正式发布于 2026-09-14；本版本的消费结果见 [RELEASING](RELEASING.md)。历史章节只描述各自版本，不替代当前接入契约。

- `releaseState`：`FORMAL`
- `binarySourceCommit`（SDK 二进制源码提交）：`82d8cab58eba588104eee9bc89063952a277af65`
- `releaseMetadataCommit`（仅回填 checksum、扫描汇总和发布验收事实，不是 SDK 二进制源码提交）：`b1bc50e272c29dd817cfcee8bbeeb9d60dfaca89`
- `artifactCandidateId`：`17cccada18787f54c2faca204769d245a3ee29adf40f6c85c679896c28f16ba4`
- `YTIFLYADLib.xcframework.zip` 的 SwiftPM checksum/SHA-256：`d5a4e2ecb1fc8495df33ed8ad37b765ca66af4cfd689eec0caf4c5424e8baf83`；`YTIFLYADLib-6.3.5.zip` 的 SHA-256：`ab3ed76a2f80ae65c0c8d5b7d6cf0d34ba26380c5b8ea020d305d82445f30631`；`checksums.txt` 的 SHA-256：`a163e9fca74cd9e833f5858cf86f8597ed8b7e77b987258033e1d7ebd7b1d38a`。
- `releaseState=FORMAL` 表示正式签名资产、checksum 和 A/B 元数据已经冻结；`delivery-manifest.json` 同步绑定提交 A。
- 同步开屏加载代次、回调保护、全交互回流、视频暂停恢复和终态资源清理；插屏加强视频任务身份与回调重入保护，素材验真在后台执行并复核文件身份。
- 共享图片下载支持订阅独立取消；加强日志脱敏和 Release 裁剪，Debug 时间线不进入正式包。继续只保留 Splash、Interstitial 和图片 / 视频能力。
- Apple Review 扫描未执行且不是发布门禁：`requiredForRelease=false`、`statusAtFreeze=not-run`、`evidenceIncluded=false`；未扫描不得表述为通过。

## 6.3.1（2026-09-01）

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
