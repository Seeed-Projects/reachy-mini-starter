### 一、 核心调试方法论：手动接管模式 (The Takeover SOP)

当后台服务（Systemd）因为网络或配置问题无法正常工作时，不要盲目重启。请按以下“三步走”接管控制权：

**1. 阻断 (Stop)**
停止后台自动运行的守护进程，释放端口（如 8000）和资源。

```bash
sudo systemctl stop reachy-mini-daemon.service

```

**2. 侦察与清理 (Scout & Clean)**
确保没有残留进程占用端口（这是导致 `Address already in use` 的元凶）。

```bash
# 查端口
sudo lsof -i :8000
# 杀进程
sudo kill -9 <PID>
# 退出残留的 screen
screen -X -S <SessionID> quit

```

**3. 注入与手动启动 (Inject & Run)**
在前台手动运行，利用工具（Proxychains）和环境变量（Export）注入网络能力，直观查看报错日志。

```bash
# 激活环境
source /venvs/mini_daemon/bin/activate
# 补全依赖 (修复摄像头推流)
export GST_PLUGIN_PATH=$GST_PLUGIN_PATH:/opt/gst-plugins-rs/lib/aarch64-linux-gnu/
# 带代理启动 (穿透网络)
proxychains4 python -m reachy_mini.daemon.app.main --wireless-version --no-autostart

```

---

### 二、 存储危机应对：16GB SD 卡生存指南

树莓派 16GB 卡极易爆满，导致安装失败 (`No space left on device`)。

**1. 快速诊断**

```bash
# 宏观查看
df -h
# 抓出大文件夹
du -sh /home/pollen/.cache/* | sort -hr

```

**2. 极速瘦身（清理缓存三剑客）**
安装失败后，必须清理这些垃圾才能重试：

```bash
# 清理 pip 安装包缓存
rm -rf /home/pollen/.cache/pip
# 清理 uv 下载缓存
rm -rf /home/pollen/.cache/uv
# 清理 HuggingFace 模型缓存
rm -rf /home/pollen/.cache/huggingface

```

---

### 三、 下载与网络策略矩阵 (Download Strategy)

针对国内网络环境下载 Python 库和 HuggingFace 模型，我们总结了三套策略，需灵活切换：

| 策略 | 适用场景 | 优点 | 缺点 | 关键配置命令 |
| --- | --- | --- | --- | --- |
| **A. 自建/私有镜像** | **首选**。通过 `w0x7ce.eu` 下载。 | 速度最快，无需代理。 | 可能**缺包**（如刚才的 `red_light` 找不到文件）。 | `export PIP_INDEX_URL=https://pypi.w0x7ce.eu/simple`<br>

<br>`export HF_ENDPOINT=https://hf.w0x7ce.eu` |
| **B. 公共镜像** | **备选**。清华源/HF-Mirror。 | 速度快，包较全。 | 偶尔会有同步延迟。 | `export PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple`<br>

<br>`export HF_ENDPOINT=https://hf-mirror.com` |
| **C. 官方源 + 代理** | **兜底**。当镜像缺包时使用。 | **最稳**，绝对有包。 | 速度受限于代理带宽，慢。 | **1. 清除变量：** `unset HF_ENDPOINT`<br>

<br>**2. 加代理启动：** `proxychains4 python ...` |

---

### 四、 最终固化 (Persistence)

当你手动调试一切正常（网络通了、包下好了），想让机器人以后**开机自启**也能正常工作，需要修改 Systemd 服务文件：

**命令：**

```bash
sudo systemctl edit reachy-mini-daemon.service

```

**填入内容（示例）：**

```ini
[Service]
# 网络代理 (让 daemon 能联网)
Environment="http_proxy=http://192.168.137.1:7890"
Environment="https_proxy=http://192.168.137.1:7890"
Environment="no_proxy=localhost,127.0.0.1,reachy-mini.local"
# 必要的运行库
Environment="GST_PLUGIN_PATH=/opt/gst-plugins-rs/lib/aarch64-linux-gnu/"

```

**生效重启：**

```bash
sudo systemctl daemon-reload
sudo systemctl restart reachy-mini-daemon.service

```

---

**下一步建议：**
现在你已经回退到了 **“策略 C（官方源+代理）”** 正在重新下载 `red_light_green_light`。
如果这次下载成功，并且你想长期玩这个机器人，强烈建议：

1. **买一张 64GB 的 SD 卡**（克隆系统过去）。
2. 或者插一个 **U 盘**，把 `/venvs` 迁移到 U 盘上，彻底解决空间焦虑。