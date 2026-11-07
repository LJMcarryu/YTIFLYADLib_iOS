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
            checksum: "69b58d7b62f9ae1645ef7c58ace2db1949e8574a2ac01e7fd8d6ce7e96e59d69"
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
