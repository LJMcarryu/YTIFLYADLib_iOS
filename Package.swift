// swift-tools-version:5.9

// 优推（YT）媒体定制 Model B 单包分发清单。
// 静态 binaryTarget 不投递外置资源，因此同名产品同时包含资源 target。

import PackageDescription

let package = Package(
    name: "YTIFLYADLib",
    platforms: [
        .iOS("11.0"),
    ],
    products: [
        .library(
            name: "YTIFLYADLib",
            targets: ["YTIFLYADLib", "YTIFLYADLibResources"]
        ),
    ],
    targets: [
        .binaryTarget(
            name: "YTIFLYADLib",
            url: "https://download-adsdk.voiceads.cn/ios_sdk/6.4.6/yt/YTIFLYADLib.xcframework.zip",
            checksum: "7362f924db37a4459c542d897fc11969d6d01127de83346e18ebea2d2c697171"
        ),
        .target(
            name: "YTIFLYADLibResources",
            path: "spm/YTIFLYADLibResources",
            resources: [
                .copy("YTAdvSDK.bundle"),
            ]
        ),
    ]
)
