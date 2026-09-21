# Antigravity 简体中文汉化补丁（Windows 适配版）

> 适配 Google Antigravity 桌面客户端（Windows 平台，已实测兼容 **v2.13.0 ~ v2.15.1** 最新版本），提供开箱即用的一键汉化、多版本自适应、安全回退与防误翻保护机制。

---

## 💖 致谢与开源声明

- 本项目基于 [@MIMICTE](https://github.com/MIMICTE) 的开源项目 [MIMICTE/Antigravity-zh-CN](https://github.com/MIMICTE/Antigravity-zh-CN) 深度演进适配。
- 衷心感谢原作者 **MIMICTE** 早期为社区开拓并搭建的优秀汉化基础！
- 本仓库遵循 **MIT License** 开源协议，针对 **Windows 平台最新版本（v2.15.1）** 进行了深度适配、词典全面扩充（640+ 条目）、新版向导与菜单汉化以及多版本自适应安全机制升级。

---

## ✨ 核心特性

- 🎯 **精准汉化**：全面覆盖常规、应用、外观、模型配额、工具权限、自定义项、浏览器子智能体等主要设置页面及系统原生菜单栏、系统托盘、启动加载遮罩与欢迎引导向导。
- 🛡️ **正文保护（防误翻）**：智能跳过 AI 对话正文（包括 `role="article"`）、代码块、终端输出、编辑器输入框和用户提示词，**绝不影响大模型生成的内容与提示词**。
- 📦 **安全解包与无损还原**：
  - 自动备份官方原版文件为 `app.asar.zh-cn-<版本号>.bak`；
  - 提供一键安全还原脚本，还原时严格比对文件哈希；
  - **100% 保持官方静默升级通道**：保留官方 `updater.js` 原生逻辑，官方后台推送升级后客户端仍可正常更新。
- ⚡ **极简操作**：提供免命令行的 Windows 双击脚本，支持 `py` 与 `python` 命令，一键自动打补丁与启动。

---

## 🚀 安装与使用

### 前置要求
- 支持 **Windows 平台 Antigravity 桌面客户端（已测试 2.13.0 ~ 2.15.1）**（不适用于 Antigravity IDE）。
- 电脑已安装 **Python 3.11 或以上**（安装时勾选添加到系统环境变量 `PATH`，支持自带的 `py` 启动器）。

### 1. 一键安装
1. 保存当前未完成的工作，在 Windows 任务栏右下角**右键 Antigravity 托盘图标**并选择 **退出应用**（仅关闭窗口可能仍有后台进程）。
2. 下载本项目后，双击运行 **`Install-zh-CN.cmd`**。
3. 脚本会自动进行环境检测、官方文件解包打补丁，并在完成后自动重启 Antigravity 展现中文界面。

### 2. 一键还原（卸载汉化）
1. 正常退出 Antigravity 应用。
2. 双击运行 **`Restore-zh-CN.cmd`**，即可瞬间无损恢复为官方原版英文状态。

> 默认程序安装路径为：`%LOCALAPPDATA%\Programs\antigravity`

---

## 🛠️ 进阶：命令行操作（供开发者）

如果你习惯使用命令行或希望自行构建与测试：

```powershell
# 1. 运行单元测试（测试 ASAR 解析、锁定与安全回退逻辑）
python -m unittest -v test_patcher.py

# 2. 构建补丁包（自动检测或指定版本）
python patcher.py --build build/2.15.1-release

# 3. 校验补丁完整性
python patcher.py --verify build/2.15.1-release

# 4. 安装补丁
python patcher.py --install build/2.15.1-release

# 5. 还原官方原版
python patcher.py --restore
```

- 词典文件：`translations.json`（完整统一词典，含 640+ 词条）
- DOM 注入引擎：`localization.js`
- 核心补丁引擎：`patcher.py`

---

## ⚠️ 免责声明

1. 本项目仅为学习研究与界面中文化使用，**仅包含开源补丁源码与翻译词典**，绝不分发或包含任何 Google 官方专有的二进制程序文件。
2. Google Antigravity 的软件著作权、商标及相关权利归 Google 官方所有。
3. 不承诺 100% 覆盖所有极罕见的网络错误及未来在线动态拉取的插件文案。
