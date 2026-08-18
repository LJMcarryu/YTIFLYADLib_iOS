# 发布流程

YT SDK 由私有源码仓 `LJMcarryu/IFLYADLibDemo` 的 `main` 单一源码生成。本仓不接收 SDK 私有源码或手工替换的二进制。

## 正式发布唯一入口

新版本正式发布只能从私有源码仓根目录的 `scripts/release-orchestrator.py` 发起，并按 `prepare → preflight → publish → verify → closeout` 顺序完成。本仓 `.github/scripts/**`、GitHub Actions `workflow_dispatch` 和各类打包命令只是底层门禁或故障诊断入口，不能替代编排器 receipt，也不得从本公开仓手工创建或移动 tag、发布 Release。

## 6.2.4 状态

- `releaseState`：`FORMAL`
- `binarySourceCommit`（SDK 二进制源码提交）：`b0f745d582ce2bed5110702cff972be4153e5038`
- `releaseMetadataCommit`（仅回填 checksum、扫描汇总和发布验收事实，不是 SDK 二进制源码提交）：`7b08118b43a0c4441de4c76a64f34fa54b3fe889`
- `candidateId`：`61f427469346615982e0225fad8187611794cc0a54c452da83073e89fd5ea1bd`

正式签名二进制、SwiftPM checksum、真实 A/B 提交和 `delivery-manifest.json` 已完成冻结并公开；`YTIFLYADLib.xcframework.zip` 的 SwiftPM checksum/SHA-256 为 `5f3df44ec856f9e38c584311512ede168cf2c0ec45e3d09378052e1b0196e263`，`YTIFLYADLib-6.2.4.zip` 的 SHA-256 为 `5207fbc790d055af81f6c33d8558ce3d1e834875e3cd283cb4ccb8dc34d35de9`。[GitHub Release 6.2.4](https://github.com/LJMcarryu/YTIFLYADLib_iOS/releases/tag/6.2.4) 的 4 个资产已完成无 Token 匿名校验，正式消费 [Run 32027223281](https://github.com/LJMcarryu/YTIFLYADLib_iOS/actions/runs/32027223281) 为 `success`。

`releaseState=FORMAL` 表示正式签名资产、checksum 和 A/B 元数据已经冻结；`delivery-manifest.json` 同步绑定提交 A。
公开可用性以同版本 GitHub Release 和发布后 CI 为准。

正式态采用两提交模型：二进制及 SwiftPM 资源均从提交 A 构建；提交 B 只回填 checksum、扫描汇总和验收事实，必须是 A 的后代。当前 `main` 的 `release-state.json` 为 `6.2.4/CLOSED`；后续 Candidate 必须由编排器从该关闭态推进到新版本 `FROZEN`，并包含真实 checksum、两个不同的真实 A/B 提交和精确资产库存。旧版 CLOSED 或非 FROZEN 状态不允许触发 candidate 或正式复验。

本版本未执行主动 Apple Review 扫描，该扫描不属于发布门禁；冻结状态为 `requiredForRelease=false`、`statusAtFreeze=not-run`、`evidenceIncluded=false`，不得表述为通过，也不代表最终宿主合规、`Validate App` 或 Apple 审核通过。

## 候选与正式资产契约

候选 Draft 和正式 Release 都必须精确包含：

```text
YTIFLYADLib.xcframework.zip
YTIFLYADLib-6.2.4.zip
checksums.txt
delivery-manifest.json
```

消费工作流同时支持：

- `validation_mode=draft_candidate`：只允许从精确 `release-candidate/6.2.4-<candidateId>` 分支触发，使用专用只读 Token 下载绑定 Release ID 的 Draft 资产；
- `validation_mode=formal_release`：只接受已公开 annotated tag，不携带 Token 匿名下载四资产。

工作流须校验两个 zip 的同源 XCFramework、资源包、请求地址、双切片、iOS 11.0、非 ad-hoc 签名、framework Bundle ID、公开头/类符号能力边界，并实际构建 CocoaPods Demo 与 SwiftPM 最小消费端。

## 私有仓底层产物诊断

以下仅供编排器调用或故障定位，不是独立正式发布入口：

```bash
IFLY_NEW_VERSION_RELEASE=1 \
IFLY_SDK_CODESIGN_IDENTITY='正式 SDK 签名身份' \
scripts/package-yt-release.sh --version 6.2.4
```

底层门禁至少必须证明：

- `YTIFLYADLib` 的两个 framework 切片 `CFBundleIdentifier` 都为 `com.gameley.www.YouTuiAdSDK`；
- device 为 arm64，simulator 为 arm64/x86_64，最低 iOS 11.0；
- 只存在 Splash、Interstitial 入口头和类符号，不存在 Banner、Reward、NativeFeed；
- `adRequestURL=https://msdk.voiceads.cn/sdk/req`，`customAdRequestURL=false`；
- `YTAdvSDK.bundle/PrivacyInfo.xcprivacy` 存在且与仓库 SwiftPM 资源完全一致；
- `delivery-manifest.json` 的 `distribution=YT`、`variant=YTSplashInterstitial`、`moduleName=YTIFLYADLib`、`capabilities=[Splash, Interstitial]`、`videoEnabled=true` 绑定同一源码提交。

`6.2.4` 不沿用历史风险接受名单；Apple Review 扫描策略为 `failOnWarning=true`、`strict=true`、`requireManual=true`、`acceptedWarningRuleIds=[]`。本版扫描未执行且不是发布门禁；未扫描不得表述为通过，也不代表最终宿主合规或 Apple 审核通过。

已发布 tag 和 zip 不允许覆盖重打；任何二进制变化都必须发布新版本。
