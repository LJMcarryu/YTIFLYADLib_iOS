# YTIFLYADLib iOS SDK 接入说明

`YTIFLYADLib` 是优推（YT）媒体定制的 iOS 广告 SDK，仅提供开屏和插屏广告，两种广告均支持图片与视频素材。Banner、激励视频和自渲染信息流不在本产物中，对应公开头、类符号和专属资源会从最终包物理裁剪。

当前最新公开正式版为 [`6.2.3`](https://github.com/LJMcarryu/YTIFLYADLib_iOS/releases/tag/6.2.3)，已于 2026-08-16 发布。正式签名资产、checksum 和 A/B 元数据已冻结；`YTIFLYADLib-6.2.3.zip` 的 SHA-256 为 `64e168120aac5f412ab96bdef78fff14e7ba75aae234a08d737fa5ad21c3e537`。annotated tag 解引用到 `09148ce3c651b3dfc35cae3c873baab6d8105950`，4 个资产已通过无 Token 匿名验证，正式消费 [Run 31941599341](https://github.com/LJMcarryu/YTIFLYADLib_iOS/actions/runs/31941599341) 为 `success`。最低支持 iOS 11.0，正式产物包含 arm64 真机与 arm64/x86_64 模拟器切片。

<!-- 供发布 CI 机器校验的两提交 provenance；README、CHANGELOG、RELEASING 必须保持一致。 -->
- `releaseState`：`FORMAL`
- `binarySourceCommit`（SDK 二进制源码提交）：`ea0240e620b57d7275e486199099c648f51de257`
- `releaseMetadataCommit`（仅回填 checksum、扫描汇总和发布验收事实，不是 SDK 二进制源码提交）：`0f26b7647e6c1aadb32eca68b24f6845639a59c2`
- `releaseState=FORMAL` 表示正式签名资产、checksum 和 A/B 元数据已经冻结。
- 公开可用性以同版本 GitHub Release 和发布后 CI 为准。
- 本提交是 `6.2.3` 的不可变发布目标。

本版本未执行主动 Apple Review 扫描，该扫描不属于发布门禁；冻结状态为 `requiredForRelease=false`、`statusAtFreeze=not-run`、`evidenceIncluded=false`，不得表述为通过，也不代表最终宿主合规、`Validate App` 或 Apple 审核通过。

## 白标契约

- framework、module 和 Mach-O：`YTIFLYADLib`
- framework `CFBundleIdentifier`：`com.gameley.www.YouTuiAdSDK`
- Objective-C 类、协议和类型前缀：`YTIFLY*`
- 公开方法及 delegate 回调首段前缀：`ytifly_`
- 伞头：`#import <YTIFLYADLib/YTIFLYADLib.h>`
- 资源包：`YTAdvSDK.bundle`
- 运行期日志前缀：`[YTAd]`
- 普通请求地址：`https://msdk.voiceads.cn/sdk/req`，不提供公开运行时 URL setter

本版不承诺与通用版、YS 版、优酷版或其他定制版在同一 App 中共存。

## 分发产物

正式 `6.2.3` Release 精确包含四个资产：

| 文件 | 内容 | 适用方式 |
| --- | --- | --- |
| `YTIFLYADLib-6.2.3.zip` | `YTIFLYADLib.xcframework`、`YTAdvSDK.bundle`、`LICENSE` | CocoaPods、手动接入 |
| `YTIFLYADLib.xcframework.zip` | 仅静态 XCFramework | SwiftPM binary target |
| `checksums.txt` | 两个 zip 的 SHA-256 及 SwiftPM checksum | 完整性校验 |
| `delivery-manifest.json` | 源码提交、构建、签名、能力与资产身份 | 发布验收 |

`YTIFLYADLib` 是静态 framework，无需 Embed；最终 App 链接必须包含 `-ObjC`。CocoaPods 清单会传播该参数并复制资源包；SwiftPM 产品会自动投递资源包，但宿主仍需添加 `-ObjC`；手动接入还需把 `YTAdvSDK.bundle` 加入 Copy Bundle Resources。

## CocoaPods

使用已发布的 `6.2.3` tag：

```ruby
source 'https://cdn.cocoapods.org/'
platform :ios, '11.0'

target 'YourApp' do
  use_frameworks!
  pod 'YTIFLYADLib',
      :podspec => 'https://raw.githubusercontent.com/LJMcarryu/YTIFLYADLib_iOS/6.2.3/YTIFLYADLib.podspec'
end
```

## Swift Package Manager

添加公开仓并选择正式版本 `6.2.3`：

```text
https://github.com/LJMcarryu/YTIFLYADLib_iOS.git
```

选择精确版本 `6.2.3` 和产品 `YTIFLYADLib`，并在 App Target 的 `Other Linker Flags` 添加 `-ObjC`。

## 手动接入

1. 下载并解压 `YTIFLYADLib-6.2.3.zip`。
2. 将 `YTIFLYADLib.xcframework` 加入 App Target，Embed 选择“Do Not Embed”。
3. 将 `YTAdvSDK.bundle` 加入 Copy Bundle Resources。
4. 将 `-ObjC` 加入 App Target 的 `Other Linker Flags`。
5. 在代码中导入 `<YTIFLYADLib/YTIFLYADLib.h>`。

## 全局配置与请求

```objc
[YTIFLYAdConfig ytifly_setPersonalizedEnabled:YES];
[YTIFLYAdConfig ytifly_setLogEnabled:NO];

YTIFLYAdRequestConfig *request = [[YTIFLYAdRequestConfig alloc] init];
request.appName = @"YourApp";
request.appVersion = @"1.0";
request.requestTimeout = @5;
```

`ytifly_setPersonalizedEnabled:` 当前只记录媒体传入的合规状态，不会自动过滤请求字段或改变广告行为。媒体应先完成自身隐私同意流程，再发起广告请求。

## 开屏广告

```objc
@interface SplashViewController () <YTIFLYSplashAdDelegate>
@property (nonatomic, strong) YTIFLYSplashAd *ad;
@end

- (void)loadSplash {
    YTIFLYSplashAd *ad = [[YTIFLYSplashAd alloc] initWithAdUnitId:@"开屏广告位 ID"];
    ad.delegate = self;
    ad.currentViewController = self;
    self.ad = ad;
    [ad ytifly_loadAd];
}

- (void)ytifly_splashAdDidReady:(YTIFLYSplashAd *)ad {
    if (ad != self.ad || ![ad ytifly_isAdValid]) return;
    [ad ytifly_showAdFromRootViewController:self];
}
```

## 插屏广告

```objc
@interface InterstitialViewController () <YTIFLYInterstitialAdDelegate>
@property (nonatomic, strong) YTIFLYInterstitialAd *ad;
@end

- (void)loadInterstitial {
    YTIFLYInterstitialAd *ad =
        [[YTIFLYInterstitialAd alloc] initWithAdUnitId:@"插屏广告位 ID"];
    ad.delegate = self;
    ad.currentViewController = self;
    self.ad = ad;
    [ad ytifly_loadAd];
}

- (void)ytifly_interstitialAdDidReady:(YTIFLYInterstitialAd *)ad {
    if (ad != self.ad || ![ad ytifly_isAdValid]) return;
    YTIFLYInterstitialAdConfig *config = [[YTIFLYInterstitialAdConfig alloc] init];
    config.presentationStyle = YTIFLYInterstitialPresentationStyleHalfScreen;
    [ad ytifly_showAdFromRootViewController:self config:config];
}
```

## 隐私与 ATT

`YTAdvSDK.bundle/PrivacyInfo.xcprivacy` 随资源包投递。宿主仍需根据自身实际数据处理在 App Store Connect 中合并申报隐私标签。iOS 14 及以上如需使用 IDFA，须配置 `NSUserTrackingUsageDescription` 并先取得 ATT 授权；未授权时传入的 IDFA 不会留待授权后复用。CocoaPods 显式链接 `AdSupport`并弱链接 `AppTrackingTransparency`。

本仓发布门禁通过不代表最终宿主合规、`Validate App` 或 Apple 审核通过。
