import Foundation

/// SwiftPM 资源定位入口。
///
/// SDK 会自动在 App 资源目录及 SwiftPM 生成的外层资源包中查找
/// `YTAdvSDK.bundle`；媒体通常无需直接访问本属性。
public enum YTIFLYADLibResources {
    public static let bundle = Bundle.module
}
