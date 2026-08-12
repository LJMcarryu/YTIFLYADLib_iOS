// swift-tools-version:5.9

// Release CI 将本次二进制和受版本控制的资源复制到本清单旁，
// 以真实本地 binaryTarget 验证 SwiftPM 产品及资源 Target。

import PackageDescription

let package = Package(
    name: "YTIFLYADLibReleaseValidation",
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
            path: "YTIFLYADLib.xcframework"
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
