# Reachy Mini Usage and Debugging Guide

This document provides core debugging methods, storage management, and network download strategies for Reachy Mini robot.

---

## Table of Contents

1. [Core Debugging Methodology](#1-core-debugging-methodology-manual-takeover-mode)
2. [Storage Crisis Management](#2-storage-crisis-management-16gb-sd-card-survival-guide)
3. [Download and Network Strategy](#3-download-and-network-strategy-matrix)
4. [Configuration Persistence](#4-configuration-persistence)

---

## 1. Core Debugging Methodology: Manual Takeover Mode

When the background service (Systemd) cannot work normally due to network or configuration issues, do not reboot blindly. Follow these "three steps" to take control.

### 1.1 Stop

Stop the background daemon service to free up ports (such as 8000) and resources.

```bash
sudo systemctl stop reachy-mini-daemon.service
```

### 1.2 Scout & Clean

Ensure no residual processes are occupying ports (this is the main cause of `Address already in use`).

```bash
# Check ports
sudo lsof -i :8000

# Kill process
sudo kill -9 <PID>

# Quit residual screen
screen -X -S <SessionID> quit
```

### 1.3 Inject & Run

Run manually in the foreground, using tools (Proxychains) and environment variables (Export) to inject network capabilities and view error logs directly.

```bash
# Activate environment
source /venvs/mini_daemon/bin/activate

# Complete dependencies (fix camera streaming)
export GST_PLUGIN_PATH=$GST_PLUGIN_PATH:/opt/gst-plugins-rs/lib/aarch64-linux-gnu/

# Start with proxy (bypass network)
proxychains4 python -m reachy_mini.daemon.app.main --wireless-version --no-autostart
```

---

## 2. Storage Crisis Management: 16GB SD Card Survival Guide

The Raspberry Pi 16GB card is easily filled, causing installation failures (`No space left on device`).

### 2.1 Quick Diagnosis

```bash
# Macro view
df -h

# Find large folders
du -sh /home/pollen/.cache/* | sort -hr
```

### 2.2 Quick Slimming (Cache Cleaning Trio)

After installation fails, you must clean these caches before retrying:

```bash
# Clean pip installation cache
rm -rf /home/pollen/.cache/pip

# Clean uv download cache
rm -rf /home/pollen/.cache/uv

# Clean HuggingFace model cache
rm -rf /home/pollen/.cache/huggingface
```

---

## 3. Download and Network Strategy Matrix

For downloading Python libraries and HuggingFace models in domestic network environments, we summarize three strategies that need to be flexibly switched.

| Strategy | Use Case | Pros | Cons | Key Configuration Commands |
|----------|----------|------|------|---------------------------|
| **A. Self-built/Private Mirror** | **First choice**. Download via `w0x7ce.eu` | Fastest, no proxy needed | May **lack packages** (e.g., `red_light` file not found) | `export PIP_INDEX_URL=https://pypi.w0x7ce.eu/simple`<br>`export HF_ENDPOINT=https://hf.w0x7ce.eu` |
| **B. Public Mirror** | **Alternative**. Tsinghua/HF-Mirror | Fast, relatively complete | Occasional sync delay | `export PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple`<br>`export HF_ENDPOINT=https://hf-mirror.com` |
| **C. Official Source + Proxy** | **Fallback**. When mirror lacks packages | **Most stable**, guaranteed packages | Speed limited by proxy bandwidth, slow | **1. Clear variables:** `unset HF_ENDPOINT`<br>**2. Start with proxy:** `proxychains4 python ...` |

---

## 4. Configuration Persistence

When manual debugging is normal (network works, packages downloaded), and you want the robot to work normally on **boot** in the future, you need to modify the Systemd service file.

### Configuration Steps

**1. Edit service file:**

```bash
sudo systemctl edit reachy-mini-daemon.service
```

**2. Fill in content (example):**

```ini
[Service]
# Network proxy (allow daemon to access internet)
Environment="http_proxy=http://192.168.137.1:7890"
Environment="https_proxy=http://192.168.137.1:7890"
Environment="no_proxy=localhost,127.0.0.1,reachy-mini.local"

# Required runtime libraries
Environment="GST_PLUGIN_PATH=/opt/gst-plugins-rs/lib/aarch64-linux-gnu/"
```

**3. Apply and restart:**

```bash
sudo systemctl daemon-reload
sudo systemctl restart reachy-mini-daemon.service
```

---

## Recommendations

Now you have reverted to **"Strategy C (Official Source + Proxy)"** and are re-downloading `red_light_green_light`.

If this download succeeds and you want to play with this robot long-term, it is strongly recommended to:

1. **Buy a 64GB SD card** (clone the system over)
2. Or plug in a **USB drive** and migrate `/venvs` to the USB drive to completely solve space anxiety
