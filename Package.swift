// swift-tools-version:5.9

// 优推（YT）定制 SDK；product 自动包含资源与隐私清单。
// 在宿主 App target 的 Other Linker Flags 中添加 -ObjC。

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
            url: "https://download-adsdk.voiceads.cn/ios_sdk/6.5.4/yt/YTIFLYADLib.xcframework.zip",
            checksum: "8f44d044c6fde38a4f42c2f4e703e623cd6df0c44eac9b08ae65628db6f434a0"
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
