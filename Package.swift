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
            url: "https://github.com/LJMcarryu/YTIFLYADLib_iOS/releases/download/6.2.3/YTIFLYADLib.xcframework.zip",
            checksum: "64892a95762bd19c77e6366422dbe81a4ff2c74b3a55f6e9c26c32afb0a135dc"
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
