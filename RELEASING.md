# 发布维护说明

## 当前发布：6.5.0

> **6.5.0 分发已完成，发布状态为 `FAST_UNVERIFIED`。** TOS 资产、公开仓 `main`/`6.5.0` Tag、CocoaPods trunk 和静态接入网站均已完成；发布结果与验证结果分开记录。

<!-- ifly-release-status: {"version":"6.5.0","status":"FAST_UNVERIFIED","distribution":"tos","releaseUrl":"https://download-adsdk.voiceads.cn/ios_sdk/6.5.0/yt/fast-release-record.json"} -->

资产回执：[6.5.0 极速发布记录](https://download-adsdk.voiceads.cn/ios_sdk/6.5.0/yt/fast-release-record.json)。网站接入指南：[当前渠道指南](https://download-adsdk.voiceads.cn/yt/)。补验记录见私有仓 `docs/需求设计/发布验收/6.5.0SwiftPM接入验证.md`；已覆盖模拟器接入、链接和资源核对，不能据此声称真机运行、广告填充或 Apple 审核通过。

## 日常发布

日常发版在私有仓根目录使用唯一入口。新版本必须使用未发布的 `x.y.z`，不能复用已有版本、Tag 或 TOS 资产：

```bash
.venv-tos/bin/python3 scripts/fast-release.py build-upload \
  --version <新版本> --channel all --publish
```

该命令按“编译/打包 → TOS → 公开仓 `main`/Tag → CocoaPods trunk → 静态网站”顺序执行。`--publish` 默认包含 trunk 和网站；显式跳过任一项会保留未完成状态，不能写成全发布 `complete`。网站包含 trunk 安装指引，trunk 未完成时应同时使用 `--skip-cocoapods-trunk --skip-site`，待 trunk 完成后用原回执 `resume` 补齐。

打包完成后的发布失败或中断，沿用同一份 `fast-release.json` 续跑，不重新编译；构建失败须先修复编译错误，再创建新一轮构建：

```bash
.venv-tos/bin/python3 scripts/fast-release.py resume --from '/绝对路径/fast-release.json'
.venv-tos/bin/python3 scripts/fast-release.py status --from '/绝对路径/fast-release.json'
.venv-tos/bin/python3 scripts/fast-release.py status --from '/绝对路径/fast-release.json' --json
.venv-tos/bin/python3 scripts/fast-release.py site --from '/绝对路径/fast-release.json' --refresh
```

`status` 只读显示资产、Git、trunk、网站和独立验证状态；`resume` 只补未完成步骤；`site --refresh` 只从本轮 `publicDirectory` 的本地文档重生成和上传网站，不自动 `git pull`、不重建或上传 SDK、不推送 Git、不发布 trunk。历史 `upload --from` / `publish --from` 仍可兼容旧回执。

## 完整验收与历史

需要完整正式验收时，按私有仓 `docs/技术方案/发布工程/正式发布流程与统一编排.md` 执行；本文件的极速发布状态不替代正式验收。

更详细的历史操作保留在本仓 Git 历史与 [CHANGELOG](CHANGELOG.md)。已发布 Tag、TOS 资产和历史回执保持不变，不修改旧版本。
