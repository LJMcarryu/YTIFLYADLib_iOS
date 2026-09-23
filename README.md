# YTIFLYADLib iOS SDK

`YTIFLYADLib` 是优推（YT）媒体定制的 iOS 广告 SDK，提供开屏和插屏，两种格式均支持图片与视频素材。本仓库提供安装入口、接入说明和可运行的 Objective-C 示例。

## 从哪里开始

- 首次接入：按本文的[安装](#安装)和[请求前配置](#请求前配置)完成工程设置。
- 先运行示例：阅读 [YTIFLYADLibSimple 使用说明](YTIFLYADLibSimple/README.md)，替换广告位后体验加载、展示和回调。
- 接入广告：[开屏](#开屏广告)、[插屏](#插屏广告)和[生命周期](#生命周期与回调)。
- 排查问题：[常见问题](#常见问题)；版本变化见 [CHANGELOG](CHANGELOG.md)。

## 当前版本与能力

<!-- ifly-release-status: {"schemaVersion":1,"version":"6.3.5","releaseState":"FORMAL","distribution":"github-release","releaseUrl":"https://github.com/LJMcarryu/YTIFLYADLib_iOS/releases/tag/6.3.5"} -->

## 6.4.0 候选联调说明

<!-- ifly-release-candidate: {"schemaVersion":1,"version":"6.4.0","releaseState":"CANDIDATE","publicationState":"UNPUBLISHED","repository":"LJMcarryu/YTIFLYADLib_iOS","currentFormalVersion":"6.3.5"} -->

`6.4.0` 目前是待联调候选，尚未发布。当前公开正式版和生产依赖仍为 [`6.3.5`](https://github.com/LJMcarryu/YTIFLYADLib_iOS/releases/tag/6.3.5)；已发布的 Tag、Release 和资产不追溯改变。

- 公开 API 方法签名不变。
- 共享 UIScene 适配将展示、落地页、外跳回流、曝光判断和 UI 生命周期绑定到广告的实际来源 window/Scene。没有来源时，仅在前台应用 Scene 唯一且明确时兜底，不跨 Scene 随机选择；独立落地页始终属于来源 Scene。
- 开屏的 rootVC 仍须已经入窗。在 Scene 宿主中使用 `customWindow` 时，窗口必须可见、尺寸有限且为正、已经关联 Scene，并与 `rootVC.window` 属于同一 Scene；它可以不是 key window，可以使用较高 `windowLevel`，也可以不设置 rootVC。输入无效时展示失败，修正窗口后可重试。

当前正式版本为 [`6.3.5`](https://github.com/LJMcarryu/YTIFLYADLib_iOS/releases/tag/6.3.5)。生产项目请固定具体版本；使用 `main` 分支的示例时，其 `Podfile` 仍固定到该 SDK 版本。

| 广告形式 | 公开入口 | 展示方式 |
| --- | --- | --- |
| 开屏 | `YTIFLYSplashAd` | 图片或视频，SDK 渲染，可配置倒计时和底部品牌区 |
| 插屏 | `YTIFLYInterstitialAd` | 图片或视频，SDK 渲染，可选择半屏或全屏 |
| Banner、激励视频、自渲染信息流 | 本包不提供 | 请按所需能力选择对应发行包 |

## 环境与命名

| 项目 | 要求 |
| --- | --- |
| 最低系统版本 | iOS 11.0 |
| SwiftPM 清单 | 使用 Swift tools 5.9，须由支持该版本清单的 Xcode 解析 |
| framework、模块、产品名 | `YTIFLYADLib` |
| Objective-C 类与协议 | `YTIFLY` 前缀 |
| 公开方法和回调 | `ytifly_` 前缀；初始化方法和属性按各公开声明使用 |
| 资源包 | `YTAdvSDK.bundle` |
| 链接方式 | 静态 XCFramework；最终 App 保留 `$(inherited)` 并添加 `-ObjC` |

统一导入伞头：

```objc
#import <YTIFLYADLib/YTIFLYADLib.h>
```

同一个 App 只安装一份广告 SDK 发行包。`YTIFLYADLib` 不支持与通用版或其他定制版同时链接；类名前缀不同也不代表可以共存。

## 安装

CocoaPods、SwiftPM 和手动集成三选一，避免重复链接 SDK 或重复拷贝资源。

### CocoaPods

在 App 的 `Podfile` 中添加：

```ruby
source 'https://cdn.cocoapods.org/'
platform :ios, '11.0'

target 'YourApp' do
  use_frameworks!
  pod 'YTIFLYADLib',
      :podspec => 'https://raw.githubusercontent.com/LJMcarryu/YTIFLYADLib_iOS/6.3.5/YTIFLYADLib.podspec'
end
```

将 `YourApp` 改为实际 target 名称，然后执行：

```bash
pod install
open YourApp.xcworkspace
```

CocoaPods 会处理 `YTAdvSDK.bundle`、`-ObjC`、`AdSupport` 和弱链接的 `AppTrackingTransparency`。后续从 `.xcworkspace` 打开工程。当前通过公开 Podspec URL 分发，不使用仅填写 Pod 名称与版本的 trunk 安装方式。

### Swift Package Manager

1. 在 Xcode 的 **File → Add Package Dependencies** 中输入仓库地址：

   ```text
   https://github.com/LJMcarryu/YTIFLYADLib_iOS.git
   ```

2. 依赖规则选择 **Exact Version**，版本填写 `6.3.5`。
3. 将产品 `YTIFLYADLib` 加入实际使用 SDK 的 App target。
4. 在 App target 的 **Build Settings → Other Linker Flags** 中保留 `$(inherited)`，添加 `-ObjC`。

产品同时包含二进制和资源 target，资源会随包集成。不要再手动添加另一份 framework 或 `YTAdvSDK.bundle`。

### 手动集成

从 [Release 6.3.5](https://github.com/LJMcarryu/YTIFLYADLib_iOS/releases/tag/6.3.5) 下载 `YTIFLYADLib-6.3.5.zip`，解压后：

1. 将 `YTIFLYADLib.xcframework` 加入 App target 的 **Frameworks, Libraries, and Embedded Content**，选择 **Do Not Embed**。
2. 将 `YTAdvSDK.bundle` 加入 App target 的 **Copy Bundle Resources**，保留包目录名称和内容。
3. 在 **Other Linker Flags** 中保留 `$(inherited)`，添加 `-ObjC`。
4. 确认 App 已链接 `AdSupport.framework`；将 `AppTrackingTransparency.framework` 以 **Optional** 方式链接，以兼容 iOS 11～13。
5. 导入伞头，编译并确认最终 App 包中包含资源及隐私清单。

## 请求前配置

### 全局配置与隐私

SDK 无需创建全局实例。发起广告请求前，根据 App 的用户选择记录个性化状态，并按需要启用日志：

```objc
[YTIFLYAdConfig ytifly_setPersonalizedEnabled:NO]; // 示例值；按实际用户选择设置
[YTIFLYAdConfig ytifly_setLogEnabled:NO];         // 正式环境建议关闭
```

`ytifly_setPersonalizedEnabled:` 当前仅记录状态，不会过滤或改写 IDFA、CAID、UA、请求字段及广告行为，也不代替 App 的隐私同意或系统 ATT 授权。应由宿主决定何时允许加载广告、传入哪些信息。

iOS 14 及以上如需使用 IDFA，在 `Info.plist` 配置符合实际用途的说明，并由宿主在适当时机发起 ATT 请求：

```xml
<key>NSUserTrackingUsageDescription</key>
<string>用于获取广告标识符 IDFA，以便请求和展示相关广告。</string>
```

只有 ATT 为 `authorized` 时才读取、传入 IDFA；未授权时传入的值不会被接收，授权后应重新读取并设置。iOS 11～13 也应遵守系统广告跟踪设置。示例中的 ATT 流程不是完整的媒体隐私同意页面；上架前还需按实际使用情况完善 App 隐私说明、隐私标签和资源内隐私清单的集成。

### 请求参数

请求配置用于加载阶段，展示配置用于展示阶段。下面的辅助函数可放在广告页面 `.m` 文件的 `@implementation` 之前，供后续示例调用：

```objc
static YTIFLYAdRequestConfig *YTMakeRequestConfig(void) {
    YTIFLYAdRequestConfig *config = [[YTIFLYAdRequestConfig alloc] init];
    config.requestTimeout = @5;
    config.appName = NSBundle.mainBundle.infoDictionary[@"CFBundleDisplayName"]
        ?: NSBundle.mainBundle.infoDictionary[@"CFBundleName"];
    config.appVersion = NSBundle.mainBundle.infoDictionary[@"CFBundleShortVersionString"];
    return config;
}
```

| 字段 | 用途与注意事项 |
| --- | --- |
| `requestTimeout` | 请求超时，单位秒；示例为 5 秒，按业务等待预算设置 |
| `requestId` | 请求标识；不设置时 SDK 自动生成 |
| `appName`、`appVersion` | 宿主名称与版本，使用真实值 |
| `settleType` | `0` 为固定价格、`1` 为 RTB；按广告位配置设置 |
| `bidFloor` | 竞价底价，单位 CNY 元/千次展示；按实际交易约定设置 |
| `interactStatus` | `1` 开启互动、`2` 关闭互动；按接入约定设置 |
| `idfa`、`caidList`、`userAgent` | 按实际可用性与授权情况提供，不使用固定测试标识替代 |
| `deepLinkDisabled` | 设置为 `@YES` 时点击直接走落地页；不修改广告请求字段 |

不需要自定义参数时，可直接调用 `ytifly_loadAd`。使用 `ytifly_applyRequestConfig:` 只设置配置，不会发起请求；使用 `ytifly_loadAdWithRequestConfig:` 会应用配置并加载。

如素材、监测或落地页使用 HTTP，宿主的 ATS 配置可能影响访问。优先使用 HTTPS；确需 HTTP 时按实际域名和业务需求配置例外。不要将 Demo 的宽泛 ATS 示例直接作为生产配置。

## 开屏广告

页面需要强持有广告实例。完成隐私流程、页面已加入 window 且 App 处于前台后，在主线程调用 `loadSplash`。将下面的广告位占位符替换为平台分配的开屏广告位，并将上面的请求配置辅助函数放在同一 `.m` 文件中。

```objc
@interface SplashViewController : UIViewController <YTIFLYSplashAdDelegate>
@property (nonatomic, strong) YTIFLYSplashAd *splashAd;
@end

@implementation SplashViewController

- (void)loadSplash {
    [self clearSplash];
    YTIFLYSplashAd *ad = [[YTIFLYSplashAd alloc] initWithAdUnitId:@"YOUR_SPLASH_AD_UNIT_ID"];
    ad.delegate = self;
    ad.currentViewController = self;
    self.splashAd = ad;
    [ad ytifly_loadAdWithRequestConfig:YTMakeRequestConfig()];
}

- (void)ytifly_splashAdDidReady:(YTIFLYSplashAd *)ad {
    if (ad != self.splashAd || !self.view.window ||
        UIApplication.sharedApplication.applicationState != UIApplicationStateActive ||
        ![ad ytifly_isAdValid]) return;
    YTIFLYSplashAdConfig *config = [[YTIFLYSplashAdConfig alloc] init];
    config.traceDuration = 5;
    config.muteOnStart = YES;
    [ad ytifly_showAdFromRootViewController:self config:config];
}

- (void)ytifly_splashAd:(YTIFLYSplashAd *)ad didFailWithError:(YTIFLYAdError *)error {
    if (ad != self.splashAd) return;
    NSLog(@"Splash failed: %d %@", error.errorCode, error.errorDescription);
    // 结束本次开屏等待，让用户继续进入 App。
}

- (void)clearSplash {
    self.splashAd.delegate = nil;
    [self.splashAd ytifly_destroy];
    self.splashAd = nil;
}

- (void)dealloc {
    [self clearSplash];
}

@end
```

这段示例在 `DidReady` 时尝试展示。若业务还未满足展示条件，应暂存实例，在条件满足后重新检查 `ytifly_isAdValid` 再展示；离开该广告流程时调用 `clearSplash`。不要在 `viewDidAppear:` 每次触发时无条件重复请求。

| 展示配置 | 行为 |
| --- | --- |
| `traceDuration` | 倒计时 3～5 秒，默认 5 秒，越界值回退为 5 秒 |
| `mediumBottomView` | 自定义底部品牌区，媒体设置视图及高度 |
| `customWindow` | 可选；使用与当前展示页面相符的 window |
| `muteOnStart` | 视频初始静音，默认 `YES` |
| `muteButtonHidden` | 是否隐藏视频静音按钮，默认 `NO` |
| `headingInteractionEnabled` | `YES` 表示将摇一摇改为扭一扭，不代表关闭交互 |
| `showNoAds` | 是否显示“免除广告”按钮；点击后的业务处理由媒体实现 |

开屏由 SDK 挂载到宿主 window，不需要媒体自己 `presentViewController:`。倒计时关闭使用 `ytifly_splashAdDidClose:`，点击跳过使用 `ytifly_splashAdDidSkip:`；视频播放完毕和点击跳转不等于倒计时关闭。启动流程应分别处理超时、失败、跳过与关闭，避免仅等待某一个回调而阻塞进入首页。

## 插屏广告

插屏适合在业务自然停顿时展示。下例仅在 `DidReady` 后保存就绪状态，由业务在合适时机调用 `showInterstitial`；请求辅助函数与开屏相同。

```objc
@interface InterstitialViewController : UIViewController <YTIFLYInterstitialAdDelegate>
@property (nonatomic, strong) YTIFLYInterstitialAd *interstitialAd;
@end

@implementation InterstitialViewController

- (void)loadInterstitial {
    [self clearInterstitial];
    YTIFLYInterstitialAd *ad = [[YTIFLYInterstitialAd alloc] initWithAdUnitId:@"YOUR_INTERSTITIAL_AD_UNIT_ID"];
    ad.delegate = self;
    ad.currentViewController = self;
    self.interstitialAd = ad;
    [ad ytifly_loadAdWithRequestConfig:YTMakeRequestConfig()];
}

- (void)ytifly_interstitialAdDidReady:(YTIFLYInterstitialAd *)ad {
    if (ad != self.interstitialAd) return;
    // 素材就绪；由业务在适合的时机调用 showInterstitial。
}

- (void)showInterstitial {
    YTIFLYInterstitialAd *ad = self.interstitialAd;
    if (!ad || !self.view.window || self.presentedViewController ||
        UIApplication.sharedApplication.applicationState != UIApplicationStateActive ||
        self.isBeingPresented || self.isBeingDismissed || ![ad ytifly_isAdValid]) return;
    YTIFLYInterstitialAdConfig *config = [[YTIFLYInterstitialAdConfig alloc] init];
    config.presentationStyle = YTIFLYInterstitialPresentationStyleHalfScreen;
    config.muteOnStart = YES;
    config.muteButtonHidden = NO;
    [ad ytifly_showAdFromRootViewController:self config:config];
}

- (void)ytifly_interstitialAd:(YTIFLYInterstitialAd *)ad didFailWithError:(YTIFLYAdError *)error {
    if (ad != self.interstitialAd) return;
    NSLog(@"Interstitial failed: %d %@", error.errorCode, error.errorDescription);
}

- (void)clearInterstitial {
    self.interstitialAd.delegate = nil;
    [self.interstitialAd ytifly_destroy];
    self.interstitialAd = nil;
}

- (void)dealloc {
    [self clearInterstitial];
}

@end
```

`presentationStyle` 可选择 `YTIFLYInterstitialPresentationStyleHalfScreen`（默认半屏）或 `YTIFLYInterstitialPresentationStyleFullScreen`（全屏）。图片或视频由返回素材决定，与半屏/全屏选择独立。

等待上一广告关闭和页面转场完成后再展示下一条。展示、关闭或销毁后的实例不再复用；下一次请求创建新实例。不要在插屏覆盖宿主导致的每一次 `viewDidDisappear:` 中无条件销毁，否则会提前结束广告。

## 生命周期与回调

两种广告的 delegate 都是弱引用，回调在主线程触发。媒体应强持有广告对象，在主线程执行页面加载、展示和清理操作。

| 阶段 | 接入方处理 |
| --- | --- |
| `ytifly_*AdDidLoad:` | 响应解析成功，可以读取 `bidInfo`、`hasVideoTemplate`、`isLandscapeTemplate`；素材可能仍在下载 |
| `ytifly_*AdDidReady:` | 素材已就绪；展示前仍需检查 `ytifly_isAdValid` 和当前页面状态 |
| `ytifly_*AdDidShow:` | 广告已展示；与有效曝光分开记录 |
| `ytifly_*AdDidExpose:` | 有效曝光回调，不要用加载或展示回调替代 |
| 点击与 `didJumpWithSuccess:` | 分别观察用户交互和跳转结果；落地页及商店关闭有各自回调 |
| 视频开始、暂停、恢复、完播 | 仅视频素材触发；视频完播不应被直接当成广告关闭 |
| `didFailWithError:` | 统一处理失败；播放、渲染细分回调按具体公开协议补充 |
| 关闭、跳过或不再使用 | 按广告格式结束业务流程；清理时置空 delegate、调用 `ytifly_destroy` 并释放引用 |

`ytifly_destroy` 可以重复调用，但已销毁实例不能重新加载。不要用固定延时替代 `DidReady`，不要对同一个实例重复展示。详细回调签名和可选方法以安装版本的 framework 公开头为准。

## 服务端竞价与结果通知

普通接入使用前述加载流程。已开通服务端竞价（S2S）的媒体，可先生成 SDK token 并按平台约定提交到媒体服务端：

```objc
NSError *error = nil;
NSString *sdkToken = [YTIFLYAdSDK ytifly_getSdkTokenWithAdUnitId:@"YOUR_AD_UNIT_ID" error:&error];
if (sdkToken.length == 0) {
    NSLog(@"SDK token failed: %@", error.localizedDescription);
    return;
}
```

服务端竞胜后，将返回的 `rspToken` 交给已设置 delegate 且由页面持有的开屏或插屏实例：

```objc
[ad ytifly_loadAdWithServerBiddingToken:rspToken];
```

之后仍等待 `DidReady` 并检查有效性再展示。空 token、过期、重复使用或已消耗 token 会失败；不要将同一 token 用于重试。S2S 成功加载后的 `bidInfo.price` 固定为 `0`，不用于还原服务端成交价。

普通 Header Bidding 场景中，可在 `DidLoad` 后读取公开竞价信息，并在媒体完成竞价决策后按约定通知结果：

```objc
NSNumber *price = ad.bidInfo.price;
NSString *dealId = ad.bidInfo.dealId;
[ad ytifly_sendBidResultWithType:YTIFLYAdBidResultTypeWin reason:@"win"];
```

`bidInfo` 只提供 `price` 和 `dealId`；未加载或无广告时可能为 `nil`。`Win` 示例只用于实际获胜，未获胜或超时应使用对应结果类型。token、价格和交易标识不要写入公开问题附件。

## 常见问题

| 现象 | 排查步骤 |
| --- | --- |
| 找不到模块或头文件 | 确认已安装依赖、target 选择正确、CocoaPods 使用 `.xcworkspace`，并导入 `YTIFLYADLib` 伞头 |
| 链接时报重复符号 | 检查是否同时安装了不同接入方式、通用版或其他定制版 |
| 方法找不到或运行时异常 | 检查最终 App target 的 `-ObjC` 和 `$(inherited)` 是否保留 |
| 资源缺失或样式异常 | 检查 `YTAdvSDK.bundle` 是否随依赖投递；手动接入时检查 Copy Bundle Resources |
| `70204` 无填充 | 请求无广告返回；核对广告位、应用绑定、请求条件及投放状态，业务正常继续 |
| `70400` 或 `71005` | 核对广告位是否合法、是否为空，以及是否匹配该 App 和广告形式 |
| `71003` 或 `71006` | 检查网络、ATS 和超时预算；使用有间隔且次数有限的重试 |
| 已收到 `DidLoad`，仍不能展示 | 等待 `DidReady`；检查素材下载错误和 `ytifly_isAdValid` |
| `71406` / `71603` | 插屏/开屏未就绪，等待有效的就绪实例 |
| `71407` / `71408` / `71409` / `71601` | 广告过期、已使用或已关闭；清理旧实例并重新创建 |
| `71410` / `71604` | 展示控制器不可用；检查前台状态、window 和页面转场 |
| IDFA 为空 | 检查系统 ATT 状态和用途说明，授权后重新读取；模拟器不能代替真实设备验证 |
| 已开启日志但看不到请求 JSON | 发布版 SDK 仅保留错误和诊断输出，日志开关不会恢复已裁剪的详细日志 |
| HTTP 素材或落地页不可访问 | 根据错误确认是否受 ATS 限制，再按实际需要配置 |

## 反馈与支持

请在 [Issues](https://github.com/LJMcarryu/YTIFLYADLib_iOS/issues) 提供 SDK 版本、iOS 与 Xcode 版本、安装方式、广告形式、复现步骤、错误码和必要的脱敏日志。可使用 `[YTIFLYAdTool ytifly_sdkVersion]` 获取实际 SDK 版本。

公开附件请去除 IDFA、CAID、完整 token、用户信息和含敏感参数的 URL。示例运行步骤、按钮行为和自查清单见 [Simple 使用说明](YTIFLYADLibSimple/README.md)；许可证见 [LICENSE](LICENSE)。
