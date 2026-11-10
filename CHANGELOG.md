# 版本记录

## [6.5.0] - 更新说明

> `6.5.0` 已验证 CocoaPods、SwiftPM 的安装、版本锁定与模拟器构建；真机广告展示需在宿主 App 中联调。

<!-- ifly-release-status: {"version":"6.5.0","status":"FAST_UNVERIFIED","distribution":"tos","releaseUrl":"https://download-adsdk.voiceads.cn/ios_sdk/6.5.0/yt/fast-release-record.json"} -->

> 以下为历史版本记录，验收结论仅适用于各节明确列出的历史版本。

## [6.4.6] - TOS 分发

本版 SDK 二进制改由火山云 TOS 分发，下载基础地址为 `https://download-adsdk.voiceads.cn/ios_sdk/6.4.6/yt`。SwiftPM 与 CocoaPods 的公开版本入口保持，生产项目固定 `6.4.6`。从共享源码重新构建，包含点击字段 `ids_a` / `__IDS_A__`、CAID 时间字段和加速度计不可用守卫；旧版本不能据此解释为已包含这些变化。

下载文件与校验值见[版本下载记录](https://download-adsdk.voiceads.cn/ios_sdk/6.4.6/yt/release-record.json)。

> 以下为历史版本记录，其中当前版本和验收结论仅适用于各自历史版本。

## [6.4.4] - 发布工程优化

- `releaseState`：`FORMAL`

历史版本：[`6.4.4`](https://github.com/LJMcarryu/YTIFLYADLib_iOS/releases/tag/6.4.4)

### 变更

- 全渠道统一为 `6.4.4`，从同一共享源码重新构建，公开 API 方法签名、广告能力和最低 iOS 11.0 要求保持。

## [6.4.2] - 冻结与发布记录

> 以下为 `6.4.2` 历史记录；其中“当前”“本版”均只指该历史版本。

历史版本：[`6.4.2`](https://github.com/LJMcarryu/YTIFLYADLib_iOS/releases/tag/6.4.2)

## 6.4.1 - 发布工程优化

> 以下为 `6.4.1` 历史记录；其中“当前”“本版”均只指该历史版本。

历史版本：[Release 6.4.1](https://github.com/LJMcarryu/YTIFLYADLib_iOS/releases/tag/6.4.1)

### 变更

- 增加匿名逐资产恢复、正式 consumer 受控恢复、摘要日志和运行耗时证据。
- SDK 与 UI 行为继承 `6.4.0`，没有新增公开 API。

## 6.4.0 冻结与发布记录

历史版本：[Release 6.4.0](https://github.com/LJMcarryu/YTIFLYADLib_iOS/releases/tag/6.4.0)

### 变更

- 共享 UIScene 适配：展示、落地页、外跳回流、曝光判断和 UI 生命周期使用广告的实际来源 window/Scene；完全没有来源时，只允许唯一且明确的前台应用 Scene，不跨 Scene 随机兜底。独立落地页始终归属来源 Scene。
- 收紧开屏 `customWindow` 的 Scene 宿主验收：rootVC 仍须入窗；`customWindow` 必须可见、尺寸有限且为正、已关联 Scene，并与 `rootVC.window` 同 Scene。合法窗口可以不是 key window，可以使用较高 `windowLevel`，也可以没有 rootVC。
- 无 Scene、跨 Scene、隐藏或尺寸无效的 `customWindow` 会导致展示失败；失败不锁死本次机会，媒体修正后可以重试。
- 公开 API 方法签名不变。

## 6.3.5

正式发布于 2026-09-14；本版本的消费结果见 [RELEASING](RELEASING.md)。历史章节只描述各自版本，不替代当前接入契约。

- `releaseState`：`FORMAL`
- `YTIFLYADLib.xcframework.zip` 的 SwiftPM checksum/SHA-256：`d5a4e2ecb1fc8495df33ed8ad37b765ca66af4cfd689eec0caf4c5424e8baf83`；`YTIFLYADLib-6.3.5.zip` 的 SHA-256：`ab3ed76a2f80ae65c0c8d5b7d6cf0d34ba26380c5b8ea020d305d82445f30631`；`checksums.txt` 的 SHA-256：`a163e9fca74cd9e833f5858cf86f8597ed8b7e77b987258033e1d7ebd7b1d38a`。
- 同步开屏加载代次、回调保护、全交互回流、视频暂停恢复和终态资源清理；插屏加强视频任务身份与回调重入保护，素材验真在后台执行并复核文件身份。
- 共享图片下载支持订阅独立取消；加强日志脱敏和 Release 裁剪，Debug 时间线不进入正式包。继续只保留 Splash、Interstitial 和图片 / 视频能力。

## 6.3.1（2026-09-01）

- `releaseState`：`FORMAL`
- `YTIFLYADLib.xcframework.zip` 的 SwiftPM checksum/SHA-256：`7adf06f9c3f1d6fe915679322ccb941ba9122edf496c9815db12db3f4e459855`；`YTIFLYADLib-6.3.1.zip` 的 SHA-256：`c47eb332cc58c864b49b3a17f594debf80f4259a9b8123b7b437ff1657fe6f1f`；`checksums.txt` 的 SHA-256：`2a42ddd0da3656729e486e90e81bcd39c7a631a4432778e1fd50ae52d41c5c2f`。
- YT 不包含 NativeFeed 和 Banner；本版从统一提交 A 重建，仅同步共享 Core 诊断与安全网，不新增被裁剪格式的公开能力。

## 6.3.0（2026-08-25）

- `releaseState`：`FORMAL`
- `YTIFLYADLib.xcframework.zip` 的 SwiftPM checksum/SHA-256：`144d0c649c1a83d8572e4a3a1295ec0430a65b788554fe62cccf6c12631a0aa5`；`YTIFLYADLib-6.3.0.zip` 的 SHA-256：`e422b4b7ed238136e90b596e4958bbabf59649dd656e38f394248b7efdb638f6`。
- 公开可用性以同版本 GitHub Release 和发布后 CI 为准。
- `release-state.json` 在 `main` 继续保留历史 `6.2.4/CLOSED`；编排器生成的候选必须是 `6.3.0/FROZEN`。
- YT 不包含 NativeFeed，本版不引入外部 CTA、媒体交互优先或结构化 `71503` 行为变化；仍从统一提交 A 重建。
- 本版继续只包含 Splash、Interstitial 与图片/视频能力，白标、Bundle ID、资源、日志和通用请求地址契约不变。

## 6.2.4（2026-08-17）

- `releaseState`：`FORMAL`
- `YTIFLYADLib.xcframework.zip` 的 SHA-256 为 `5f3df44ec856f9e38c584311512ede168cf2c0ec45e3d09378052e1b0196e263`；`YTIFLYADLib-6.2.4.zip` 的 SHA-256 为 `5207fbc790d055af81f6c33d8558ce3d1e834875e3cd283cb4ccb8dc34d35de9`。
- [GitHub Release 6.2.4](https://github.com/LJMcarryu/YTIFLYADLib_iOS/releases/tag/6.2.4) 的 4 个资产已完成无 Token 匿名校验，正式消费 [Run 32027223281](https://github.com/LJMcarryu/YTIFLYADLib_iOS/actions/runs/32027223281) 为 `success`。

## 6.2.3

- `releaseState`：`FORMAL`
- 公开可用性以同版本 GitHub Release 和发布后 CI 为准。

- 首次发布优推（YT）独立公开分发仓。
- framework/module 为 `YTIFLYADLib`，framework Bundle ID 为 `com.gameley.www.YouTuiAdSDK`。
- 类型、方法、资源和日志白标为 `YTIFLY*`、`ytifly_*`、`YTAdvSDK.bundle`、`[YTAd]`。
- 定制版仅保留开屏、插屏和图片/视频素材能力；物理裁剪 Banner、Reward 和 NativeFeed。
- 普通请求固定使用通用地址 `https://msdk.voiceads.cn/sdk/req`，`customAdRequestURL=false`。
- 提供 CocoaPods、SwiftPM 和手动接入产物，正式 Release 资产库存固定为四项。
- 正式签名产物和 checksum 已冻结并公开；`YTIFLYADLib-6.2.3.zip` 的 SHA-256 为 `64e168120aac5f412ab96bdef78fff14e7ba75aae234a08d737fa5ad21c3e537`。[GitHub Release 6.2.3](https://github.com/LJMcarryu/YTIFLYADLib_iOS/releases/tag/6.2.3) 的 annotated tag 解引用到 `09148ce3c651b3dfc35cae3c873baab6d8105950`，4 个资产已通过无 Token 匿名验证与正式消费 [Run 31941599341](https://github.com/LJMcarryu/YTIFLYADLib_iOS/actions/runs/31941599341)。
