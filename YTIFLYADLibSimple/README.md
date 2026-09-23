# YTIFLYADLibSimple 使用说明

本工程演示 `YTIFLYADLib 6.3.5` 的开屏与插屏接入，使用 Objective-C 和 SDK 公开 API。页面提供加载、展示、状态检查、销毁及回调日志，便于先跑通广告生命周期，再迁移到媒体 App。

SDK 的安装方式、隐私语义、完整接入示例和错误说明见[根目录接入文档](../README.md)。本示例没有 Banner、激励视频或自渲染信息流入口。

> `6.4.0` 当前是待联调候选，尚未发布；本示例的 `Podfile` 继续固定公开正式版 `6.3.5`，因此直接运行示例时不会获得候选行为。历史 Tag、Release 和资产保持不变。
>
> 使用后续候选产物联调时，公开 API 方法签名不变。展示、落地页、外跳回流、曝光判断和 UI 生命周期应归属广告的实际来源 window/Scene；无来源时只允许唯一且明确的前台应用 Scene，不跨 Scene 随机兜底，独立落地页始终属于来源 Scene。开屏 rootVC 仍须入窗；Scene 宿主的 `customWindow` 必须可见、尺寸有限且为正、已关联 Scene，并与 `rootVC.window` 同 Scene，可以是非 key、高 `windowLevel`、无 rootVC。非法输入展示失败，修正后可以重试。

## 运行前准备

- 安装 Xcode、命令行工具与 CocoaPods；最低部署版本为 iOS 11.0。
- 准备平台分配的开屏、插屏广告位，确认广告位对应的 App、Bundle Identifier、广告形式和投放配置。
- 准备可访问 GitHub 与广告服务的网络。模拟器可验证编译和基础流程；IDFA、外部 App 跳转与真实填充需在设备上验证。
- 明确宿主的隐私同意和 ATT 授权时机。Demo 会在 App 首次进入活动状态时尝试系统 ATT 请求，不提供完整的媒体隐私同意界面。

## 从下载到运行

### 1. 获取工程并安装依赖

```bash
git clone https://github.com/LJMcarryu/YTIFLYADLib_iOS.git
cd YTIFLYADLib_iOS/YTIFLYADLibSimple
pod install
open YTIFLYADLibSimple.xcworkspace
```

已有仓库时，直接进入其中的 `YTIFLYADLibSimple` 目录执行最后两条命令。`pod install` 会生成 workspace；后续都从 `.xcworkspace` 打开。

`Podfile` 已固定到 `6.3.5` 的公开 Podspec：

```ruby
pod 'YTIFLYADLib', :podspec => 'https://raw.githubusercontent.com/LJMcarryu/YTIFLYADLib_iOS/6.3.5/YTIFLYADLib.podspec'
```

CocoaPods 自动处理静态 framework、`YTAdvSDK.bundle`、`-ObjC`、`AdSupport` 及弱链接的 `AppTrackingTransparency`，无需再手动 Embed framework 或添加资源副本。

### 2. 替换广告位

修改 [`YTIFLYAdPrefixHeader.pch`](<YTIFLYADLibSimple/Supporting Files/YTIFLYAdPrefixHeader.pch>) 中的宏：

| 宏 | 页面入口 | 需要填写的内容 |
| --- | --- | --- |
| `__SPLASH_NATIVE_AD_UNIT_ID__` | 开屏 → 图片开屏 | 本 App 的图片开屏广告位；宏名中的 `NATIVE` 不表示自渲染信息流 |
| `__SPLASH_VIDEO_AD_UNIT_ID__` | 开屏 → 视频开屏 | 本 App 的视频开屏广告位 |
| `__INTERSTITIAL_AD_UNIT_ID__` | 插屏 → 半屏/全屏 | 本 App 的插屏广告位；图片或视频由返回素材决定 |

仓库中的 ID 仅用于演示，不能保证任何时刻都有填充，也不应直接用于生产 App。切换开屏选项后需要重新点 `Load`，已加载素材不会因切换选项而改变。

### 3. 检查请求与隐私配置

[`YTIFLYADUtil.m`](<YTIFLYADLibSimple/Supporting Files/YTIFLYADUtil.m>) 的 `mediaSampleRequestConfig` 集中配置：

| 示例值 | 接入时如何处理 |
| --- | --- |
| `requestTimeout = @5` | 根据页面等待预算设置，单位秒 |
| `settleType = @1` | 示例采用 RTB，按实际广告位交易方式修改 |
| `bidFloor = @0.01` | 示例底价，单位 CNY 元/千次展示，按实际约定修改 |
| `interactStatus = @1` | 示例开启互动，按实际业务与广告位配置修改 |
| `appName` / `appVersion` | 从当前 App 信息读取，检查与媒体应用一致 |
| `idfa` | 每次构建请求配置时检查授权后读取；未授权或全零 IDFA 不传入 |

[`AppDelegate.m`](YTIFLYADLibSimple/AppDelegate.m) 记录个性化状态并开启调试日志。`ytifly_setPersonalizedEnabled:` 只记录状态，不控制数据采集、请求字段或 ATT 授权；迁移时应在宿主完成自身隐私流程后再允许广告加载，并按用户实际选择设置该值。

[`Info.plist`](YTIFLYADLibSimple/Info.plist) 已包含 ATT 用途说明和较宽泛的 ATS 示例。正式 App 应使用自身用途文案，并按实际 HTTP 需求配置 ATS。Debug 页面日志便于调试；对外分享时需去除广告位、交易标识等敏感信息。

### 4. 配置签名并运行

1. 选择 `YTIFLYADLibSimple` scheme。
2. 模拟器运行：选择本机已安装的 iPhone 模拟器，执行 **Product → Run**。
3. 真机运行：在 App target 的 **Signing & Capabilities** 中选择自己的 Team，设置可签名且与媒体配置一致的 Bundle Identifier，再选择设备运行。
4. 首页确认实际 SDK 版本为 `6.3.5`，进入开屏或插屏页面。

仅检查模拟器构建时，可在本目录执行：

```bash
xcodebuild build \
  -workspace YTIFLYADLibSimple.xcworkspace \
  -scheme YTIFLYADLibSimple \
  -configuration Debug \
  -destination 'generic/platform=iOS Simulator' \
  CODE_SIGNING_ALLOWED=NO
```

此命令验证编译与链接；真实填充、展示效果和点击跳转仍需运行 App 检查。

## 页面操作

### 开屏

1. 选择“图片开屏”或“视频开屏”。
2. 点 `Load`，页面先显示“正在加载开屏”，收到 `splashAdDidLoad` 后显示等待素材就绪。
3. 收到 `splashAdDidReady` 后 `Show` 才可用。
4. 点 `Show` 展示；示例倒计时为 5 秒，底部有媒体品牌区，视频初始静音且显示静音按钮。
5. 观察展示、曝光、点击跳转、倒计时关闭或跳过回调。完成本次流程后，再点 `Load` 创建下一条广告。

示例故意采用手动展示，便于观察阶段；实际启动页应在合适的业务时机展示，并设置失败、跳过、关闭和超时后进入首页的处理。SDK 负责将开屏挂载到 window，媒体不需要自行 present 开屏控制器。

### 插屏

1. 选择“半屏”或“全屏”；这是展示样式，不是素材类型开关。
2. 点 `Load`，等待 `interstitialAdDidReady`。
3. 点 `Show`，SDK 按当前选中的样式展示广告。
4. 观察 `DidShow`、`DidRender`、`DidExpose`、点击和关闭日志。
5. 关闭后如需下一条广告，再点 `Load`，不要重复展示旧实例。

插屏会覆盖宿主页面；返回宿主后，应等待转场结束再触发下一次展示。素材是否为视频、模板是否横版可在加载日志中查看。

### 公共按钮和日志

| 操作/信息 | 实际行为 |
| --- | --- |
| `Load` | 先清理旧实例，再创建新实例并请求；测试时等待结果，避免连续点击 |
| `Show` | 重新检查 `ytifly_isAdValid`，未就绪或失效时不展示 |
| `Destroy` | 置空 delegate、销毁实例、释放引用并禁用 Show；再次测试须点 Load |
| 检查状态 | 输出可展示状态以及已返回的 `bidInfo.price` / `bidInfo.dealId`；未加载时可能为空 |
| 回调日志 | 页面按时间追加，可选中文本；Debug 控制台还可搜索 `[YTAdSample]` |
| 页面退出 | 控制器释放时销毁持有的广告；迁移时按自己的页面生命周期显式清理 |

页面只实现常用回调，并未逐项记录视频暂停/恢复等所有可选方法。需要额外事件时，按安装版本的 `YTIFLYSplashAdDelegate` / `YTIFLYInterstitialAdDelegate` 补充。发布版 SDK 开启日志后仅输出错误和诊断，不能恢复详细请求 JSON。

## 代码阅读路径

| 文件 | 用途 |
| --- | --- |
| [`AppDelegate.m`](YTIFLYADLibSimple/AppDelegate.m) | window、导航、全局配置及 ATT 示例 |
| [`ViewController.m`](YTIFLYADLibSimple/ViewController.m) | 首页、SDK 版本和两种广告入口 |
| [`YTIFLYAdPrefixHeader.pch`](<YTIFLYADLibSimple/Supporting Files/YTIFLYAdPrefixHeader.pch>) | 三个广告位和示例日志宏 |
| [`YTIFLYADUtil.m`](<YTIFLYADLibSimple/Supporting Files/YTIFLYADUtil.m>) | 公共请求配置、授权后 IDFA 读取、日志和 UI 辅助方法 |
| [`YTIFLYSplashViewController.m`](YTIFLYADLibSimple/biz/splash/YTIFLYSplashViewController.m) | 开屏加载、展示配置、清理和回调 |
| [`YTIFLYInterstitialViewController.m`](YTIFLYADLibSimple/biz/interstitial/YTIFLYInterstitialViewController.m) | 插屏加载、半屏/全屏、清理和回调 |
| [`Podfile`](Podfile) | SDK 版本与安装来源 |

迁移时保留“强持有实例 → 设置 delegate → 加载 → DidReady → 检查有效性 → 展示 → 清理”的顺序。Demo 的页面布局、辅助方法和广告位宏可以替换为自己的业务实现。

## 建议自查

- 首页 SDK 版本正确，工程没有重复链接的 framework 或缺失资源提示。
- 使用自己的图片/视频开屏广告位，分别观察 Load、Ready、Show 和结束流程。
- 使用插屏广告位，分别观察半屏与全屏、关闭后重新加载。
- 在素材未就绪、请求失败、无填充或广告失效时，业务可以继续且不会无限重试。
- Destroy 后旧实例不再触发页面展示；离开页面后不会由迟到回调弹出广告。
- 真机检查 ATT 同意/拒绝、前后台切换、视频静音、落地页及外部 App 返回。

构建成功只说明该工程能够编译链接。没有广告返回时，先查看失败回调，不要仅凭空白页面判断 SDK 安装失败。

## 常见问题

| 现象 | 处理 |
| --- | --- |
| `pod install` 失败 | 检查 CocoaPods、网络和 Podspec/Release URL，保留第一条实际下载或解析错误；不要改成 trunk 安装 |
| 找不到 `YTIFLYADLib` | 先安装依赖，再打开 workspace；确认 scheme 和 target 正确 |
| 真机签名失败 | 选择自己的 Team，检查 Bundle Identifier、设备注册与签名证书 |
| 收到 `70204` | 当前无填充；检查广告位和投放，按业务策略稍后重试 |
| `Show` 一直不可用 | 查找 `DidReady` 或失败日志；`DidLoad` 仅表示响应解析成功 |
| 切换图片/视频后仍是旧素材 | 重新点 Load，选项仅决定下一次请求使用的广告位 |
| 切换插屏半屏/全屏没有获得视频 | 展示样式不决定素材类型，检查广告位返回的素材 |
| IDFA 为空或 ATT 未弹出 | 查看系统授权状态；已选择过时不重复弹窗，拒绝时不传 IDFA；用真机验证 |
| 点击或播放表现与模拟器不同 | 使用已配置的真机与广告位验证网络、外部 App、音频和系统权限 |

更多错误码及处理方式见[根目录常见问题](../README.md#常见问题)。反馈问题时附 SDK/iOS/Xcode 版本、安装方式、广告形式、复现步骤和脱敏后的错误日志。
