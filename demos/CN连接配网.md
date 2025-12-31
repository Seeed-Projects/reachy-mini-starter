# Reachy Mini 网络连接配置指南

在 Ubuntu 上使用命令行 (CLI) 实现网络共享的标准作业程序 (SOP)。

---

## 场景描述

**连接方式**：
```
树莓派 <---> Hub(USB转网口) <---> 网线 <---> Ubuntu 电脑网口 (enp45s0)
```

**目标**：Ubuntu 电脑通过 Wi-Fi 上网，并将网络**共享**给网口，让树莓派获得 IP (`10.42.0.x`) 并能上网。

---

## 目录

1. [快速配置步骤](#快速配置步骤)
2. [验证与连接](#验证与连接)
3. [重要提示](#重要提示)
4. [参考信息](#参考信息)

---

## 快速配置步骤

### 步骤 1：确认接口名称与连接名

首先查看网卡名称和对应的连接名字（NAME）。

```bash
nmcli device
```

**目标**：找到 `TYPE` 为 `ethernet` 的那一行。

**假设结果**：DEVICE 是 `enp45s0`，CONNECTION 是 `Wired connection 1`。

---

### 步骤 2：开启"共享"模式 (关键)

将该有线连接的 IPv4 模式修改为 `shared`（相当于 Windows 的"允许其他用户通过此计算机连接"）。

```bash
nmcli connection modify "Wired connection 1" ipv4.method shared
```

---

### 步骤 3：重启接口生效

配置修改后必须重启接口才能启动 DHCP 服务。

```bash
nmcli connection down "Wired connection 1"
nmcli connection up "Wired connection 1"
```

---

### 步骤 4：验证本机 IP (网关)

确认 Ubuntu 网口是否变成了网关 IP（通常是 `10.42.0.1`）。

```bash
ifconfig enp45s0
# 或者
ip addr show enp45s0
```

---

## 验证与连接

### 步骤 5：扫描树莓派 IP

扫描 `10.42.0.x` 网段，寻找除了 `.1` 以外的设备。

```bash
sudo nmap -sn 10.42.0.0/24
```

**如果没有安装 nmap**，可以使用以下替代方法：

```bash
# 方法 1: 使用 arp
arp -n

# 方法 2: 查看 DHCP 租约
cat /var/lib/misc/dnsmasq.leases
```

---

### 步骤 6：SSH 连接

拿到 IP（比如 `10.42.0.75`）后，直接登录。

```bash
ssh pollen@10.42.0.75
```

---

## 重要提示

### 永久生效

这个配置是**永久的**。下次你把树莓派拔了，过几天再插上，只要还是插在这个网口，Ubuntu 会自动识别并再次启动共享模式，不需要重新敲命令。

### 恢复普通网口模式

如果你以后要把这个网口插到墙上的路由器上网，记得把模式改回"自动"：

```bash
nmcli connection modify "Wired connection 1" ipv4.method auto
nmcli connection up "Wired connection 1"
```

---

## 参考信息

### 示例网络配置

**树莓派端网络状态示例：**

```
eth1: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 10.42.0.75  netmask 255.255.255.0  broadcast 10.42.0.255
        ether 6c:1f:f7:24:1f:fd  txqueuelen 1000  (Ethernet)
```

**WiFi 连接状态：**

```
wlan0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 10.57.101.85  netmask 255.255.255.0  broadcast 10.57.101.255
        ether 2c:cf:67:f8:b7:44  txqueuelen 1000  (Ethernet)
```

### WiFi 自动连接设置

确保 WiFi 配置为自动连接：

```bash
# 查看自动连接设置
nmcli connection show "YOUR_WIFI_SSID" | grep autoconnect

# 输出应为：
# connection.autoconnect:                 yes
```

### WiFi 连接命令

```bash
# 连接到 WiFi
sudo nmcli device wifi connect "SSID_NAME" password "PASSWORD"

# 查看所有连接
nmcli connection show
```

---

## 常见问题

### Q: 找不到树莓派 IP 怎么办？

A: 确认以下几点：
1. 网线是否插紧
2. Ubuntu 共享模式是否已开启
3. 树莓派是否已开机
4. 使用 `arp -n` 或查看 DHCP 租约

### Q: SSH 连接不上怎么办？

A: 检查：
1. IP 地址是否正确
2. 树莓派 SSH 服务是否运行
3. 防火墙是否阻止连接

### Q: 网络共享后树莓派无法上网怎么办？

A: 检查：
1. Ubuntu 电脑是否已连接互联网
2. Ubuntu 防火墙/NAT 设置
3. DNS 解析是否正常
