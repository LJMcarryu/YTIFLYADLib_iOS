# 发布流程

YT SDK 由私有源码仓 `LJMcarryu/IFLYADLibDemo` 的 `main` 单一源码生成。本仓不接收 SDK 私有源码或手工替换的二进制。

## 正式发布唯一入口

新版本正式发布只能从私有源码仓根目录的 `scripts/release-orchestrator.py` 发起，并按 `prepare → preflight → publish → verify → closeout` 顺序完成。本仓 `.github/scripts/**`、GitHub Actions `workflow_dispatch` 和各类打包命令只是底层门禁或故障诊断入口，不能替代编排器 receipt，也不得从本公开仓手工创建或移动 tag、发布 Release。

## 6.2.3 状态

- `releaseState`：`FORMAL`
- `binarySourceCommit`（SDK 二进制源码提交）：`c90c8e969b05d4d55b522cb162ab0f2e37aacc52`
- `releaseMetadataCommit`（仅回填 checksum、扫描汇总和发布验收事实，不是 SDK 二进制源码提交）：`b340fe7cccc27af37fc6223042f9638e507a4b63`

`releaseState=FORMAL` 表示正式签名资产、checksum 和 A/B 元数据已经冻结；公开可用性以同版本 GitHub Release 和发布后 CI 为准。

正式签名二进制、SwiftPM checksum、真实 A/B 提交已完成本地冻结校验；公开可用性以同版本 GitHub Release 和发布后 CI 为准。

正式态采用两提交模型：二进制及 SwiftPM 资源均从提交 A 构建；提交 B 只回填 checksum、扫描汇总和验收事实，必须是 A 的后代。Candidate 必须已经包含真实 checksum、`releaseState=FORMAL` 和两个不同的真实 A/B 提交；未冻结的占位 checksum 不允许触发 candidate 或正式复验。

## 候选与正式资产契约

候选 Draft 和正式 Release 都必须精确包含：

```text
YTIFLYADLib.xcframework.zip
YTIFLYADLib-6.2.3.zip
checksums.txt
delivery-manifest.json
```

消费工作流同时支持：

- `validation_mode=draft_candidate`：只允许从精确 `release-candidate/6.2.3-<candidateId>` 分支触发，使用当次 GitHub Token 下载绑定 Release ID 的 Draft 资产；
- `validation_mode=formal_release`：只接受已公开 annotated tag，不携带 Token 匿名下载四资产。

工作流须校验两个 zip 的同源 XCFramework、资源包、请求地址、双切片、iOS 11.0、非 ad-hoc 签名、framework Bundle ID、公开头/类符号能力边界，并实际构建 CocoaPods Demo 与 SwiftPM 最小消费端。

## 私有仓底层产物诊断

以下仅供编排器调用或故障定位，不是独立正式发布入口：

```bash
IFLY_NEW_VERSION_RELEASE=1 \
IFLY_SDK_CODESIGN_IDENTITY='正式 SDK 签名身份' \
scripts/package-yt-release.sh --version 6.2.3
```

底层门禁至少必须证明：

- `YTIFLYADLib` 的两个 framework 切片 `CFBundleIdentifier` 都为 `com.gameley.www.YouTuiAdSDK`；
- device 为 arm64，simulator 为 arm64/x86_64，最低 iOS 11.0；
- 只存在 Splash、Interstitial 入口头和类符号，不存在 Banner、Reward、NativeFeed；
- `adRequestURL=https://msdk.voiceads.cn/sdk/req`，`customAdRequestURL=false`；
- `YTAdvSDK.bundle/PrivacyInfo.xcprivacy` 存在且与仓库 SwiftPM 资源完全一致；
- `delivery-manifest.json` 的 `distribution=YT`、`variant=YTSplashInterstitial`、`moduleName=YTIFLYADLib`、`capabilities=[Splash, Interstitial]`、`videoEnabled=true` 绑定同一源码提交。

`6.2.3` 不沿用历史风险接受名单；Apple Review 扫描策略为 `failOnWarning=true`、`strict=true`、`requireManual=true`、`acceptedWarningRuleIds=[]`。扫描通过不代表最终宿主合规或 Apple 审核通过。

已发布 tag 和 zip 不允许覆盖重打；任何二进制变化都必须发布新版本。
