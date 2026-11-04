# 发布流程

## 6.4.4 冻结与发布记录

<!-- ifly-release-status: {"schemaVersion":1,"version":"6.4.4","releaseState":"FORMAL","distribution":"github-release","releaseUrl":"https://github.com/LJMcarryu/YTIFLYADLib_iOS/releases/tag/6.4.4"} -->

- `releaseState`：`FORMAL`
- `binarySourceCommit`（SDK 二进制源码提交）：`25ebc73166c9596822cfcf4e93d74fc6c98bd5e4`
- `releaseMetadataCommit`（仅回填 checksum、扫描汇总和发布验收事实，不是 SDK 二进制源码提交）：`56aaeb4d5b76858b266981d30afd76bff6a73ad2`

`6.4.4` 的正式分发资料以同版本真实冻结 manifest 为准。当前正式版本：[`6.4.4`](https://github.com/LJMcarryu/YTIFLYADLib_iOS/releases/tag/6.4.4)；公开时间和消费验证结论以 `release-state.json.publication` 与同版本 GitHub Release 的实际状态为准。历史 Tag、Release 和资产保持不可变。


YT SDK 由私有源码仓 `LJMcarryu/IFLYADLibDemo` 的 `main` 单一源码生成。本仓不接收 SDK 私有源码或手工替换的二进制。

## 6.4.2 冻结与发布记录

历史记录见[历史发布记录](docs/需求设计/发布验收/历史发布记录.md#642-冻结与发布记录)。

## 正式发布唯一入口

新版本正式发布只能从私有源码仓根目录的 `scripts/release-orchestrator.py` 发起，并按 `prepare → preflight → publish → verify → closeout` 顺序完成。本仓 `.github/scripts/**`、GitHub Actions `workflow_dispatch` 和各类打包命令只是底层门禁或故障诊断入口，不能替代编排器 receipt，也不得从本公开仓手工创建或移动 tag、发布 Release。

## 6.4.1 冻结与发布记录

历史记录见[历史发布记录](docs/需求设计/发布验收/历史发布记录.md#641-冻结与发布记录)。

## 6.4.0 冻结与发布记录

历史记录见[历史发布记录](docs/需求设计/发布验收/历史发布记录.md#640-冻结与发布记录)。

## 6.3.5 状态

历史记录见[历史发布记录](docs/需求设计/发布验收/历史发布记录.md#635-状态)。

## 候选与正式资产契约

候选 Draft 和正式 Release 都必须精确包含：

```text
YTIFLYADLib.xcframework.zip
YTIFLYADLib-<目标版本>.zip
checksums.txt
delivery-manifest.json
```

消费工作流同时支持：

- `validation_mode=draft_candidate`：只允许从精确 `release-candidate/<version>-<candidateId>` 分支触发，使用专用只读 Token 下载绑定 Release ID 的 Draft 资产；
- `validation_mode=formal_release`：只接受已公开 annotated tag，不携带 Token 匿名下载四资产。

工作流须校验两个 zip 的同源 XCFramework、资源包、请求地址、双切片、iOS 11.0、非 ad-hoc 签名、framework Bundle ID、公开头/类符号能力边界，并实际构建 CocoaPods Demo 与 SwiftPM 最小消费端。

## 私有仓底层产物诊断

以下命令仅在私有源码仓用于本地诊断，输出不构成正式发布资产或 receipt。正式模式的 candidate 与构建输入由编排器提供：

```bash
VERSION='<目标版本>'
IFLY_SDK_CODESIGN_IDENTITY='<本机诊断签名身份>' \
scripts/package-yt-release.sh --version "${VERSION}"
```

底层门禁至少必须证明：

- `YTIFLYADLib` 的两个 framework 切片 `CFBundleIdentifier` 都为 `com.gameley.www.YouTuiAdSDK`；
- device 为 arm64，simulator 为 arm64/x86_64，最低 iOS 11.0；
- 只存在 Splash、Interstitial 入口头和类符号，不存在 Banner、Reward、NativeFeed；
- `adRequestURL=https://msdk.voiceads.cn/sdk/req`，`customAdRequestURL=false`；
- `YTAdvSDK.bundle/PrivacyInfo.xcprivacy` 存在且与仓库 SwiftPM 资源完全一致；
- `delivery-manifest.json` 的 `distribution=YT`、`variant=YTSplashInterstitial`、`moduleName=YTIFLYADLib`、`capabilities=[Splash, Interstitial]`、`videoEnabled=true` 绑定同一源码提交。

Apple Review 为主动可选扫描；目标版本策略以对应计划为准，未执行仅记录 `not-run`，不得表述为通过。

已发布 tag 和 zip 不允许覆盖重打；任何二进制变化都必须发布新版本。
