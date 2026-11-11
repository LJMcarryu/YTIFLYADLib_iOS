# Manual 接入示例

此独立示例固定使用 SDK `6.5.1`；仓库当前发布版本另见[根 README](../README.md)。工程包含与本仓 CocoaPods Demo 对应的广告示例页面，应用 Bundle Identifier 独立，可以分别安装对比。示例源码是生成时的独立副本。

## 运行

先准备本地库，再打开共享 workspace（需要 Python 3）：

```bash
python3 准备SDK.py
open YTIFLYADLibManualSimple.xcworkspace
```

准备脚本按 `sdk-artifacts.json` 下载并校验固定版本的官方 XCFramework，放入 `Vendor/`。工程直接链接这些本地库，不使用 SwiftPM 或 CocoaPods，Xcode 构建过程不会联网下载库。`Vendor/` 不提交 Git；已经准备好的副本可离线构建。也可以从清单中的官方链接自行下载 ZIP，再运行 `python3 准备SDK.py --archive-dir /绝对路径/下载目录`。本地库被修改时脚本会拒绝复用；确认需要重建后使用 `--refresh`。

工程按静态库方式链接 XCFramework（**Do Not Embed**）。同版资源和隐私清单保存在 `SDKResources/`，已配置 Copy Bundle Resources，不要从其他版本重复复制。不要修改隐私声明来规避系统限制。

在 Xcode 选择 **YTIFLYADLibManualSimple** scheme，再选择模拟器或真机。真机运行时设置自己的 Team 与 Bundle Identifier，替换源码 `Supporting Files` 中的广告位配置。示例 ID 不保证填充。工程最低声明 iOS 11.0，实际可用系统范围需结合所用 Xcode 与 SDK 验证。

App target 已配置 `$(inherited) -ObjC`、`AdSupport.framework` 和 Optional 的 `AppTrackingTransparency.framework`。请保留应用隐私流程与系统授权处理；构建通过不代表广告已成功加载或展示。

页面使用与各广告形式 API 见[接入指南](../docs/接入指南/README.md)；本副本的源码目录仍为 `YTIFLYADLibSimple/`。日志或请求失败须按实际回调和系统日志定位。

## 构建检查

```bash
xcodebuild -workspace YTIFLYADLibManualSimple.xcworkspace \
  -scheme YTIFLYADLibManualSimple -configuration Debug \
  -destination 'generic/platform=iOS Simulator' \
  -derivedDataPath build/DerivedData CODE_SIGNING_ALLOWED=NO build
```

## 版本维护

此示例不会随仓库当前版本自动升级。更新依赖时同时更新工程、锁文件或资产摘要、同版资源及说明，并重新验证模拟器与设备架构。不得混用不同版本的库与资源。`示例来源.json` 记录本副本的 SDK Tag 和示例源码提交。
