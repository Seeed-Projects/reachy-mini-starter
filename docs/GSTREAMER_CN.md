# 📡 GStreamer 安装指南（无线 Reachy Mini）

> 本指南将帮助您安装 [GStreamer](https://gstreamer.freedesktop.org) 以从无线 Reachy Mini 接收视频和音频流。

<div align="center">

| 🐧 **Linux** | 🍎 **macOS** | 🪟 **Windows** |
|:---:|:---:|:---:|
| ✅ 支持 | ✅ 支持 | ⚠️ 部分支持 |

</div>

## 🔧 安装 GStreamer

<details>
<summary>🐧 <strong>Linux</strong></summary>

### 步骤 1：安装 GStreamer

**适用于 Ubuntu/Debian 系统：**

在终端中运行：

```bash
sudo apt-get update
sudo apt-get install -y \
    libgstreamer-plugins-bad1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    libgstreamer1.0-dev \
    libglib2.0-dev \
    libssl-dev \
    libgirepository1.0-dev \
    libcairo2-dev \
    libportaudio2 \
    libnice10 \
    gstreamer1.0-plugins-good \
    gstreamer1.0-alsa \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-nice \
    python3-gi \
    python3-gi-cairo
```

### 步骤 2：安装 Rust

在 Linux 上，WebRTC 插件默认未启用，需要从 Rust 源代码手动编译。使用 `rustup` 从命令行安装 Rust：

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
```

### 步骤 3：构建并安装 WebRTC 插件

要构建并安装 WebRTC 插件，请运行以下命令：

```bash
# 克隆 GStreamer Rust 插件仓库
git clone https://gitlab.freedesktop.org/gstreamer/gst-plugins-rs.git
cd gst-plugins-rs
git checkout 0.14.1

# 安装 cargo-c 构建工具
cargo install cargo-c

# 创建安装目录
sudo mkdir -p /opt/gst-plugins-rs
sudo chown $USER /opt/gst-plugins-rs

# 编译并安装 WebRTC 插件（可能需要几分钟）
cargo cinstall -p gst-plugin-webrtc --prefix=/opt/gst-plugins-rs --release

# 添加插件路径到环境变量
echo 'export GST_PLUGIN_PATH=/opt/gst-plugins-rs/lib/x86_64-linux-gnu:$GST_PLUGIN_PATH' >> ~/.bashrc
source ~/.bashrc
```

> **💡 提示：** 对于 ARM64 系统（如 Raspberry Pi），请在导出命令中将 `x86_64-linux-gnu` 替换为 `aarch64-linux-gnu`。

<details>
<summary>⚠️ <strong>Ubuntu 22.04 特殊处理</strong></summary>

Ubuntu 22.04 默认使用 GStreamer 1.20，需要使用 **gst-plugins-rs 0.11.3** 版本以确保兼容性：

```bash
# 克隆 GStreamer Rust 插件仓库
git clone https://gitlab.freedesktop.org/gstreamer/gst-plugins-rs.git
cd gst-plugins-rs

# 关键点：切换到 0.11.3 版本（这是兼容 GStreamer 1.20 的最后一个稳定版）
git checkout 0.11.3

# 修复依赖库 Bug - 0.11.3 版本依赖的 time 库有 Bug，需要手动更新
cargo update -p time

# 安装 cargo-c 构建工具
cargo install cargo-c

# 创建安装目录
sudo mkdir -p /opt/gst-plugins-rs
sudo chown $USER /opt/gst-plugins-rs

# 编译并安装 WebRTC 插件（可能需要几分钟）
cargo cinstall -p gst-plugin-webrtc --prefix=/opt/gst-plugins-rs --release

# 添加插件路径到环境变量
echo 'export GST_PLUGIN_PATH=/opt/gst-plugins-rs/lib/x86_64-linux-gnu:$GST_PLUGIN_PATH' >> ~/.bashrc
source ~/.bashrc
```

**为什么需要这些特殊步骤？**

- **0.11.3 版本**：这是与 GStreamer 1.20（Ubuntu 22.04 默认版本）兼容的最后一个稳定版本
- **`cargo update -p time`**：0.11.3 版本依赖的 time 库存在 "type annotations needed" 错误，此命令会自动更新到修复版本

</details>

</details>

<details>
<summary>🍎 <strong>macOS</strong></summary>

### 使用 Homebrew

```bash
brew install gstreamer libnice-gstreamer
```

WebRTC 插件在 Homebrew 包中默认启用。

</details>

<details>
<summary>🪟 <strong>Windows</strong></summary>

> ⚠️ **注意：** Windows 目前仅部分支持。某些功能可能无法正常工作。

### 步骤 1：使用官方安装程序安装 GStreamer

<div align="center">

[![下载 GStreamer for Windows](https://img.shields.io/badge/Download-GStreamer%20for%20Windows-blue?style=for-the-badge&logo=windows&logoColor=white)](https://gstreamer.freedesktop.org/download/)

</div>

1. 下载 **运行时** 和 **开发** 安装程序（MSVC 版本）
2. 使用 **完整** 安装选项安装两者
3. 添加到系统 PATH：`C:\gstreamer\1.0\msvc_x86_64\bin`
4. 添加到 PKG_CONFIG_PATH：`C:\gstreamer\1.0\msvc_x86_64\lib\pkgconfig`

> **💡 重要提示：** 如果您将 GStreamer 安装在其他位置，请将 `C:\gstreamer` 替换为实际的安装文件夹。

### 步骤 2：安装 Rust

在 Windows 上，WebRTC 插件默认未启用，需要从 Rust 源代码手动编译。使用 Windows 安装程序安装 Rust：

1. 从 [https://rustup.rs/](https://rustup.rs/) 下载并安装 Rust
2. 重启终端。

### 步骤 3：构建并安装 WebRTC 插件

要构建并安装 WebRTC 插件，请运行以下命令：

```powershell
# 克隆 GStreamer Rust 插件仓库
git clone https://gitlab.freedesktop.org/gstreamer/gst-plugins-rs.git
cd gst-plugins-rs
git checkout 0.14.1

# 安装 cargo-c 构建工具
cargo install cargo-c

# 编译 WebRTC 插件（可能需要几分钟）
cargo cinstall -p gst-plugin-webrtc --prefix=C:\gst-plugins-rs --release

# 将插件复制到 GStreamer 插件目录
copy C:\gst-plugins-rs\lib\gstreamer-1.0\gstrswebrtc.dll C:\gstreamer\1.0\msvc_x86_64\lib\gstreamer-1.0\

# 添加插件路径到环境变量
set GST_PLUGIN_PATH="C:\gst-plugins-rs\lib\gstreamer-1.0;%GST_PLUGIN_PATH%"
```

> **💡 提示：** 如果路径不同，请将 `C:\gstreamer` 替换为实际的 GStreamer 安装路径。最后一个命令需要管理员权限才能设置系统范围的环境变量。

</details>

## ✅ 验证安装

最后，您可以按以下方式测试 GStreamer 安装：

```bash
# 检查版本
gst-launch-1.0 --version

# 测试基本功能
gst-launch-1.0 videotestsrc ! autovideosink

# 验证 WebRTC 插件
gst-inspect-1.0 webrtcsrc
```

> **💡 高级测试和故障排除：** 请参阅 [高级 Raspberry Pi 设置指南](../platforms/reachy_mini/advanced_rpi_setup.md) 了解详细的配置选项和系统诊断。

## 🔧 Python 依赖项

安装 Reachy Mini Python 包时，还需要添加 `gstreamer` 额外选项：

### 从 PyPI 安装

```bash
uv pip install "reachy-mini[gstreamer]"
```

### 从源码安装

```bash
uv sync --extra gstreamer
```
