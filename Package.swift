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
            url: "https://download-adsdk.voiceads.cn/ios_sdk/6.5.0/yt/YTIFLYADLib.xcframework.zip",
            checksum: "9460eac1d496d8309264b101db3db3feda34bb804897a1f17f95fe4e3c0b947d"
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
