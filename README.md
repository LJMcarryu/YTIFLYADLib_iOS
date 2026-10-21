# YTIFLYADLib iOS SDK

本仓库提供面向 iOS 应用的优推（YT）定制广告 SDK，包含开屏和插屏，以及安装说明和 Objective-C 示例。

当前正式版本：[`6.4.2`](https://github.com/LJMcarryu/YTIFLYADLib_iOS/releases/tag/6.4.2)。生产项目请固定具体版本。

<!-- ifly-release-status: {"schemaVersion":1,"version":"6.4.2","releaseState":"FORMAL","distribution":"github-release","releaseUrl":"https://github.com/LJMcarryu/YTIFLYADLib_iOS/releases/tag/6.4.2"} -->

[运行示例](YTIFLYADLibSimple/README.md) · [安装方式](docs/接入指南/安装方式.md) · [隐私与请求配置](docs/接入指南/隐私与请求配置.md) · [更新记录](CHANGELOG.md) · [排错](docs/接入指南/生命周期与排错.md) · [支持](#隐私许可与支持)

## 能力与接入身份

| 广告形式 | 公开入口 | 展示方式 |
| --- | --- | --- |
| 开屏 | `YTIFLYSplashAd` | SDK 渲染，图片或视频 |
| 插屏 | `YTIFLYInterstitialAd` | SDK 渲染，半屏或全屏，图片或视频 |

本包不提供 Banner、激励视频、自渲染信息流。所有格式均支持图片与视频，实际素材由广告位返回。

| 项目 | 接入值 |
| --- | --- |
| CocoaPods Pod | `YTIFLYADLib` |
| SwiftPM product | `YTIFLYADLib` |
| framework / 导入模块 | `YTIFLYADLib` |
| 外置资源 | `YTAdvSDK.bundle` |
| 链接要求 | 静态 XCFramework；最终 App 保留 `$(inherited)` 和 `-ObjC`，选择 **Do Not Embed** |
| 同一 App 的选择 | CocoaPods、SwiftPM、手动集成三选一；只安装一份 SDK 发行包 |

类和协议使用 `YTIFLY` 前缀，公开方法和回调使用 `ytifly_` 前缀；初始化方法和属性以公开声明为准。YT 不支持与通用版或其他定制版同时链接，前缀不同也不代表能够共存。

```objc
#import <YTIFLYADLib/YTIFLYADLib.h>
```

## 环境要求

| 项目 | 要求 |
| --- | --- |
| 最低系统 | iOS 11.0 |
| 二进制接入 | 能使用 XCFramework 的 Xcode |
| SwiftPM 清单 | Swift tools 5.9；需由能解析该清单的 Xcode 使用 |
| 示例 | macOS、Xcode、CocoaPods；真机需配置自己的 Team 与 Bundle ID |

包清单版本不单独代表全部 Xcode 的二进制兼容性。运行示例后的检查方法与模拟器、真机验证边界见 [Simple 指南](YTIFLYADLibSimple/README.md)；具体版本的构建及消费验证记录见同版 Release。

## 安装

推荐通过精确版本的公开 Podspec URL 安装，将 `YourApp` 替换为实际 target：

```ruby
source 'https://cdn.cocoapods.org/'
platform :ios, '11.0'

target 'YourApp' do
  use_frameworks!
  pod 'YTIFLYADLib',
      :podspec => 'https://raw.githubusercontent.com/LJMcarryu/YTIFLYADLib_iOS/6.4.2/YTIFLYADLib.podspec'
end
```

```bash
pod install
open YourApp.xcworkspace
```

CocoaPods 自动投递 `YTAdvSDK.bundle`、传播 `-ObjC` 并处理 `AdSupport` 与弱链接 `AppTrackingTransparency`。保留完整 Podspec URL，不使用仅填写 Pod 名和版本的 trunk 安装方式。

[SwiftPM 精确版本与手动集成](docs/接入指南/安装方式.md)中提供产品选择、完整包资产名、资源和链接设置。

## 最小使用流程

先取得分配给当前 App、渠道和格式的广告位，完成宿主隐私流程，再发起请求。首次接入可使用默认请求配置；交易参数仅在平台明确约定后填写，见[请求配置](docs/接入指南/隐私与请求配置.md)。

强持有广告对象并设置代理 → 调用 `ytifly_loadAd` 或 `ytifly_loadAdWithRequestConfig:` → 等待 `ytifly_*AdDidReady:` → 在业务选定的展示时机检查 `ytifly_isAdValid`、前台状态和展示页面 → 调用 `ytifly_showAdFromRootViewController:config:` → 结束后清理。

`DidLoad` 只表示数据已返回。Ready 到达时若页面暂不可展示，保留实例，在后续业务时机重新检查有效性；失效后重新创建。插屏指南提供这种加载与展示分离的代码，Simple 提供可构建的加载、展示与销毁页面。

失败、无填充或放弃等待时让业务继续；开屏分别处理等待超时、失败、跳过和关闭，并保证进入后续页面只执行一次。完成或永久放弃后置空 delegate、销毁并释放实例；不要在广告临时覆盖页面触发的 `viewDidDisappear:` 中无条件销毁。详见[生命周期与排错](docs/接入指南/生命周期与排错.md)。

Simple 实际调用开屏、插屏公开 API，使用 `Load`、`Show`、`Destroy` 分别观察加载、业务时机展示与清理。

## 按广告形式接入

| 广告形式 | 接入指南 | 示例源码与覆盖范围 |
| --- | --- | --- |
| 开屏 | [开屏指南](docs/接入指南/开屏广告.md) | [开屏页面](YTIFLYADLibSimple/YTIFLYADLibSimple/biz/splash/YTIFLYSplashViewController.m) |
| 插屏 | [插屏指南](docs/接入指南/插屏广告.md) | [插屏页面](YTIFLYADLibSimple/YTIFLYADLibSimple/biz/interstitial/YTIFLYInterstitialViewController.m) |

[服务端竞价与结果通知](docs/接入指南/服务端竞价.md)仅供已开通相应流程的媒体使用，普通接入直接使用上述加载流程。

## 隐私、许可与支持

`ytifly_setPersonalizedEnabled:` 仅记录状态，不过滤或改写 IDFA、CAID、UA、请求字段或广告行为，也不替代隐私同意与 ATT 授权。宿主控制请求时机与传入信息；iOS 14 及以上仅在 ATT `authorized` 时读取、传入 IDFA。详情见[隐私与请求配置](docs/接入指南/隐私与请求配置.md)。

[使用许可](LICENSE) · [安全问题私密报告](SECURITY.md) · [普通接入问题 Issues](https://github.com/LJMcarryu/YTIFLYADLib_iOS/issues)

反馈时提供 SDK/iOS/Xcode 版本、安装方式、广告形式、复现步骤与错误码；去除 IDFA、CAID、token、用户信息和敏感 URL。发布版日志仅保留错误与诊断，日志开关不会恢复已裁剪的请求/响应详情。

## 原章节入口

### 请求前配置

请见[请求前配置](docs/接入指南/隐私与请求配置.md)。

### 开屏广告

请见[开屏广告](docs/接入指南/开屏广告.md)。

### 插屏广告

请见[插屏广告](docs/接入指南/插屏广告.md)。

### 生命周期与回调

请见[生命周期与回调](docs/接入指南/生命周期与排错.md)。

### 服务端竞价与结果通知

请见[服务端竞价与结果通知](docs/接入指南/服务端竞价.md)。

### 常见问题

请见[常见问题](docs/接入指南/生命周期与排错.md#常见问题)。

### 反馈与支持

请见[反馈与支持](#隐私许可与支持)。
