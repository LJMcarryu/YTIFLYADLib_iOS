# 发布维护说明

## 6.4.6 TOS 发布

<!-- ifly-release-status: {"version":"6.4.6","status":"FORMAL","distribution":"tos","releaseUrl":"https://download-adsdk.voiceads.cn/ios_sdk/6.4.6/yt/release-record.json"} -->

本版 SDK 二进制改由火山云 TOS 分发，下载基础地址为 `https://download-adsdk.voiceads.cn/ios_sdk/6.4.6/yt`。SwiftPM 与 CocoaPods 的公开版本入口保持，生产项目固定 `6.4.6`。从共享源码重新构建，包含点击字段 `ids_a` / `__IDS_A__`、CAID 时间字段和加速度计不可用守卫；旧版本不能据此解释为已包含这些变化。

产物清单、大小、SHA-256、源码与元数据提交见 [TOS 发布记录](https://download-adsdk.voiceads.cn/ios_sdk/6.4.6/yt/release-record.json)。只有该记录存在且 `release-state.json` 为 `CLOSED` 才表示本版发布完成。正式证据包含匿名下载以及 SwiftPM/CocoaPods 的 simulator/device 编译链接与资源检查；普通 CI 只检查元数据。CocoaPods trunk、Apple 人工审核与真实媒体验收不在本次分发完成范围。

## 操作顺序

正式入口位于私有源码仓 `scripts/release-orchestrator.py`，显式选择对应 `release-plan-tos*.json`。依次执行 `prepare → preflight → publish → verify → closeout`，每个执行阶段均须 `--execute`。上传凭据仅保存在维护者本机的仓库外文件，不写入公开仓。

资产对象路径为 `ios_sdk/<version>/<channel>/<asset>`，版本内对象禁止覆盖；同名对象只有完整内容摘要一致才可收养。上传后从公开域名匿名下载并实际消费，成功后才推进 main、创建 annotated Tag 和写入 TOS 发布记录。失败按同一候选/修订续跑，不移动历史 Tag 或覆盖既有资产。

本仓 GitHub 仅承载清单、文档、示例和 Tag，新版本不创建 GitHub Release。历史记录见 [CHANGELOG](CHANGELOG.md) 和 [历史发布记录](docs/需求设计/发布验收/历史发布记录.md)。
