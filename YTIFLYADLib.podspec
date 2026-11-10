# 优推（YT）定制 SDK：开屏与插屏。

Pod::Spec.new do |s|
  s.name = 'YTIFLYADLib'
  s.module_name = 'YTIFLYADLib'
  s.version = '6.5.0'
  s.summary = '优推定制 YTIFLYADLib：开屏与插屏，支持图片和视频。'
  s.homepage = 'https://github.com/LJMcarryu/YTIFLYADLib_iOS'
  s.author = { 'IFLY' => '讯飞AI营销' }
  s.source = { :http => 'https://download-adsdk.voiceads.cn/ios_sdk/6.5.0/yt/YTIFLYADLib-6.5.0.zip' }
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
