# YTIFLYADLib iOS SDK

`YTIFLYADLib` 是 YT 媒体定制的 iOS 广告 SDK，仅提供开屏和插屏；两种格式均支持图片与视频素材。本产物不包含 Banner、激励视频或自渲染信息流。

## 6.3.1 发布状态

<!-- ifly-release-status: {"schemaVersion":1,"version":"6.3.1","releaseState":"FORMAL","distribution":"github-release","releaseUrl":"https://github.com/LJMcarryu/YTIFLYADLib_iOS/releases/tag/6.3.1"} -->

当前正式版本：[`6.3.1`](https://github.com/LJMcarryu/YTIFLYADLib_iOS/releases/tag/6.3.1)。生产项目请固定到具体版本，不要依赖 `main` 分支。

## 能力矩阵

| 能力 | 入口类 | 渲染方式 |
| --- | --- | --- |
| 开屏 | `YTIFLYSplashAd` | SDK 内置渲染，支持图片和视频 |
| 插屏 | `YTIFLYInterstitialAd` | SDK 内置渲染，支持半屏/全屏、图片和视频 |
| Banner | — | 本变体不提供 |
| 激励视频 | — | 本变体不提供 |
| 自渲染信息流 | — | 本变体不提供 |

## 白标命名和环境要求

- framework、module 和产品名：`YTIFLYADLib`。
- Objective-C 类和协议前缀：`YTIFLY`。
- 公开方法和 delegate 回调前缀：`ytifly_`；初始化方法和属性保持系统风格。
- 入口头：

  ```objc
  #import <YTIFLYADLib/YTIFLYADLib.h>
  ```

- 资源包：`YTAdvSDK.bundle`。
- iOS 11.0 及以上，Xcode 15.0 及以上。
- SDK 是静态 XCFramework，最终 App 必须链接 `-ObjC`，不需要 Embed & Sign。
- 不建议在同一 App 中同时集成其他白标变体；如确有需求，请先确认符号和产品名不会冲突。

## 安装

### CocoaPods

```ruby
source 'https://cdn.cocoapods.org/'
platform :ios, '11.0'

target 'YourApp' do
  use_frameworks!
  pod 'YTIFLYADLib',
      :podspec => 'https://raw.githubusercontent.com/LJMcarryu/YTIFLYADLib_iOS/6.3.1/YTIFLYADLib.podspec'
end
```

```bash
pod install
open YourApp.xcworkspace
```

CocoaPods 会自动投递 `YTAdvSDK.bundle` 并传播 `-ObjC`。

### Swift Package Manager

在 Xcode 中添加：

```text
https://github.com/LJMcarryu/YTIFLYADLib_iOS.git
```

选择版本 `6.3.1` 和产品 `YTIFLYADLib`。资源 target 会自动投递 `YTAdvSDK.bundle`；在 App target 的 `Other Linker Flags` 添加：

```text
-ObjC
```

### 手动集成

从 [Release 6.3.1](https://github.com/LJMcarryu/YTIFLYADLib_iOS/releases/tag/6.3.1) 下载 `YTIFLYADLib-6.3.1.zip`：

1. 将 `YTIFLYADLib.xcframework` 加入 App target，Embed 选择 **Do Not Embed**。
2. 将 `YTAdvSDK.bundle` 加入 **Copy Bundle Resources**。
3. 在 App target 的 `Other Linker Flags` 添加 `-ObjC`。
4. 导入 `<YTIFLYADLib/YTIFLYADLib.h>`。

## 初始化、隐私和请求配置

```objc
#import <YTIFLYADLib/YTIFLYADLib.h>

- (BOOL)application:(UIApplication *)application
    didFinishLaunchingWithOptions:(NSDictionary *)launchOptions {
    [YTIFLYAdConfig ytifly_setPersonalizedEnabled:YES];
    [YTIFLYAdConfig ytifly_setLogEnabled:NO];
    return YES;
}
```

`ytifly_setPersonalizedEnabled:` 只记录媒体侧个性化状态，不代替 ATT，也不会自动改变请求内容。正式上线建议关闭日志。

iOS 14 及以上如需使用 IDFA，请配置：

```xml
<key>NSUserTrackingUsageDescription</key>
<string>用于获取广告标识符 IDFA，以便请求和展示相关广告。</string>
```

只有 ATT `authorized` 时才读取或传入 IDFA；授权完成后重新读取。宿主仍须在 App Store Connect 隐私标签中申报 SDK 实际数据处理。

两种广告都支持 `YTIFLYAdRequestConfig`：

```objc
- (YTIFLYAdRequestConfig *)requestConfig {
    YTIFLYAdRequestConfig *config = [[YTIFLYAdRequestConfig alloc] init];
    config.requestTimeout = @5;
    config.appName = NSBundle.mainBundle.infoDictionary[@"CFBundleDisplayName"];
    config.appVersion = NSBundle.mainBundle.infoDictionary[@"CFBundleShortVersionString"];
    config.settleType = @1;  // 0=固定价格，1=RTB
    config.bidFloor = @0.01;
    return config;
}
```

常用字段还包括 `requestId`、`userAgent`、`idfa`、`caidList` 和 `deepLinkDisabled`。未设置 `requestId` 时 SDK 自动生成。

## 开屏广告

```objc
@interface SplashViewController () <YTIFLYSplashAdDelegate>
@property (nonatomic, strong) YTIFLYSplashAd *splashAd;
@end

- (void)loadSplash {
    YTIFLYSplashAd *ad = [[YTIFLYSplashAd alloc] initWithAdUnitId:@"YOUR_SPLASH_AD_UNIT_ID"];
    ad.delegate = self;
    ad.currentViewController = self;
    self.splashAd = ad;
    [ad ytifly_loadAdWithRequestConfig:[self requestConfig]];
}

- (void)ytifly_splashAdDidReady:(YTIFLYSplashAd *)ad {
    if (ad != self.splashAd || ![ad ytifly_isAdValid]) return;
    YTIFLYSplashAdConfig *config = [[YTIFLYSplashAdConfig alloc] init];
    config.traceDuration = 5;
    config.muteOnStart = YES;
    [ad ytifly_showAdFromRootViewController:self config:config];
}

- (void)ytifly_splashAd:(YTIFLYSplashAd *)ad didFailWithError:(YTIFLYAdError *)error {
    NSLog(@"Splash failed: %d %@", error.errorCode, error.errorDescription);
}
```

常用回调包括 `ytifly_splashAdDidLoad:`、`ytifly_splashAdDidReady:`、`ytifly_splashAdDidShow:`、`ytifly_splashAdDidExpose:`、`ytifly_splashAdDidClick:`、`ytifly_splashAdDidClose:`、`ytifly_splashAdDidSkip:` 和失败回调。视频素材还会触发播放状态回调。开屏挂载到 window，不使用 `presentViewController:`。

## 插屏广告

```objc
@interface InterstitialViewController () <YTIFLYInterstitialAdDelegate>
@property (nonatomic, strong) YTIFLYInterstitialAd *interstitialAd;
@end

- (void)loadInterstitial {
    YTIFLYInterstitialAd *ad = [[YTIFLYInterstitialAd alloc] initWithAdUnitId:@"YOUR_INTERSTITIAL_AD_UNIT_ID"];
    ad.delegate = self;
    ad.currentViewController = self;
    self.interstitialAd = ad;
    [ad ytifly_loadAdWithRequestConfig:[self requestConfig]];
}

- (void)ytifly_interstitialAdDidReady:(YTIFLYInterstitialAd *)ad {
    if (ad != self.interstitialAd || ![ad ytifly_isAdValid]) return;
    YTIFLYInterstitialAdConfig *config = [[YTIFLYInterstitialAdConfig alloc] init];
    config.presentationStyle = YTIFLYInterstitialPresentationStyleHalfScreen;
    config.muteOnStart = YES;
    [ad ytifly_showAdFromRootViewController:self config:config];
}

- (void)ytifly_interstitialAd:(YTIFLYInterstitialAd *)ad didFailWithError:(YTIFLYAdError *)error {
    NSLog(@"Interstitial failed: %d %@", error.errorCode, error.errorDescription);
}
```

使用 `YTIFLYInterstitialPresentationStyleHalfScreen` 或 `YTIFLYInterstitialPresentationStyleFullScreen`。展示或关闭后重新创建实例；不要在正在 present/dismiss 时重复展示。

## S2S 和 Header Bidding

如平台已开通服务端竞价，生成 SDK token：

```objc
NSError *error = nil;
NSString *sdkToken = [YTIFLYAdSDK ytifly_getSdkTokenWithAdUnitId:@"YOUR_AD_UNIT_ID" error:&error];
```

服务端返回竞胜 `rspToken` 后：

```objc
[ad ytifly_loadAdWithServerBiddingToken:rspToken];
```

加载成功后从公开字段读取竞价信息：

```objc
NSNumber *price = ad.bidInfo.price;
NSString *dealId = ad.bidInfo.dealId;
[ad ytifly_sendBidResultWithType:YTIFLYAdBidResultTypeWin reason:@"win"];
```

Token 生命周期、通知时机和失败重试策略以平台协议为准；未开通时使用普通 `ytifly_loadAd`。

## 错误处理与生命周期

- `ytifly_*AdDidLoad:` 表示响应解析成功，素材可能仍在下载。
- `ytifly_*AdDidReady:` 表示主素材已就绪，可以展示。
- 展示前检查 `ytifly_isAdValid`。
- 页面退出时置空 delegate、调用 `ytifly_destroy` 并释放强引用。
- 所有失败通过对应 delegate 的 `didFailWithError:` 返回 `YTIFLYAdError`；无填充、网络错误和超时应按业务策略结束或重试，不要无限重试。

## 示例工程

`YTIFLYADLibSimple` 只包含开屏和插屏示例，符合本变体的能力边界：

```bash
cd YTIFLYADLibSimple
pod install
open YTIFLYADLibSimple.xcworkspace
```

请替换示例广告位 ID，并在获得隐私同意后加载广告。Demo 构建成功表示包能够被正确消费和链接，不代表线上一定有填充。

## 能力边界和常见问题

| 问题 | 处理方式 |
| --- | --- |
| 找不到 Banner、Reward 或 NativeFeed 类 | 这些能力不在 YT 6.3.1 产物中，请勿从其他变体复制代码。 |
| `-ObjC` 缺失 | 在最终 App target 的 `Other Linker Flags` 添加 `-ObjC`。 |
| 内置广告在 `DidLoad` 展示失败 | 等待 `ytifly_*AdDidReady:` 并检查 `ytifly_isAdValid`。 |
| IDFA 为空 | 检查 ATT 授权和 `NSUserTrackingUsageDescription`；授权完成后重新读取。 |
| 资源缺失 | 确认 `YTAdvSDK.bundle` 已由 CocoaPods/SwiftPM 投递，或已在手动集成时加入 Copy Bundle Resources。 |

## 反馈与支持

请在 [Issues](https://github.com/LJMcarryu/YTIFLYADLib_iOS/issues) 提交问题，并附 SDK 版本、iOS/Xcode 版本、接入方式、复现步骤和错误回调。版本变更见 [`CHANGELOG.md`](./CHANGELOG.md)。
