# 优推（YT）媒体定制 Model B 单包分发。
# framework/module、类型、方法、资源分别白标为
# YTIFLYADLib、YTIFLY*、ytifly_*、YTAdvSDK.bundle。

Pod::Spec.new do |s|
  s.name = 'YTIFLYADLib'
  s.module_name = 'YTIFLYADLib'
  s.version = '6.2.3'
  s.summary = '优推定制 YTIFLYADLib：开屏与插屏，支持图片和视频。'
  s.homepage = 'https://github.com/LJMcarryu/YTIFLYADLib_iOS'
  s.author = { 'IFLY' => '讯飞AI营销' }
  s.source = { :http => 'https://github.com/LJMcarryu/YTIFLYADLib_iOS/releases/download/6.2.3/YTIFLYADLib-6.2.3.zip' }
  s.license = { :type => 'MIT', :file => 'LICENSE' }

  s.platform = :ios, '11.0'
  s.static_framework = true
  s.vendored_frameworks = 'YTIFLYADLib.xcframework'
  s.resources = ['YTAdvSDK.bundle']
  s.pod_target_xcconfig = { 'OTHER_LDFLAGS' => '$(inherited) -ObjC' }
  s.user_target_xcconfig = { 'OTHER_LDFLAGS' => '$(inherited) -ObjC' }
  s.frameworks = ['AdSupport']
  s.weak_frameworks = ['AppTrackingTransparency']
end
