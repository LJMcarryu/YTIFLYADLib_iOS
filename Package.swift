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
            url: "https://github.com/LJMcarryu/YTIFLYADLib_iOS/releases/download/6.3.1/YTIFLYADLib.xcframework.zip",
            checksum: "7adf06f9c3f1d6fe915679322ccb941ba9122edf496c9815db12db3f4e459855"
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
