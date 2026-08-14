# YTIFLYADLibSimple

本工程仅演示 `YTIFLYADLib 6.2.3` 准备版的开屏和插屏广告接入，两种格式均可展示图片或视频素材。Demo 不包含 Banner、激励视频或自渲染信息流入口。

当前 Demo 对应 `6.2.3` 候选冻结版本；`releaseState=FORMAL` 只表示资产与元数据已冻结，正式 tag、Release 与公开消费仍待编排器执行。候选/正式 CI 会将精确的合并 zip 解压为本地 Pod，实际构建该 Demo。

## 使用方式

正式发布后，在本目录执行：

```bash
pod install
open YTIFLYADLibSimple.xcworkspace
```

选择 `YTIFLYADLibSimple` scheme 运行。实际媒体接入应替换 Demo 广告位 ID，并在发起请求前完成自身隐私同意与 ATT 流程。

## Podfile

```ruby
pod 'YTIFLYADLib', :podspec => 'https://raw.githubusercontent.com/LJMcarryu/YTIFLYADLib_iOS/6.2.3/YTIFLYADLib.podspec'
```

SDK 是静态 framework，无需 Embed。`YTAdvSDK.bundle`、`-ObjC`、`AdSupport` 和弱链接的 `AppTrackingTransparency` 由 podspec 处理。

## API 命名

- 伞头：`#import <YTIFLYADLib/YTIFLYADLib.h>`
- 类型：`YTIFLYSplashAd`、`YTIFLYInterstitialAd`
- 方法：`ytifly_loadAd`、`ytifly_showAdFromRootViewController:config:`、`ytifly_destroy`
- 初始化方法与属性保持系统风格：`initWithAdUnitId:`、`ad.delegate`

## 目录

```text
YTIFLYADLibSimple/
  YTIFLYADLibSimple.xcodeproj
  YTIFLYADLibSimple/
    ViewController.*
    biz/
      splash/
      interstitial/
    Supporting Files/
  Podfile
  README.md
```
