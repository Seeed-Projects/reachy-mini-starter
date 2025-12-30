**在 Ubuntu 上使用命令行 (CLI) 实现网络共享**的全套“标准作业程序 (SOP)”。

### 场景描述

* **连接方式**：树莓派 <---> Hub(USB转网口 ) <--->  网线 <---> Ubuntu 电脑网口 (`enp45s0`)。
* **目标**：Ubuntu 电脑通过 Wi-Fi 上网，并将网络**共享**给网口，让树莓派获得 IP (`10.42.0.x`) 并能上网。

---

### 🚀 极简命令行速查表

#### 1. 确认接口名称与连接名

首先看一眼你的网卡叫什么，以及它对应的连接名字（NAME）。

```bash
nmcli device

```

* **目标**：找到 `TYPE` 为 `ethernet` 的那一行。
* *假设结果：DEVICE 是 `enp45s0`，CONNECTION 是 `Wired connection 1`。*

#### 2. 开启“共享”模式 (关键一步)

将该有线连接的 IPv4 模式修改为 `shared`（这就相当于 Windows 的“允许其他用户通过此计算机连接”）。

```bash
nmcli connection modify "Wired connection 1" ipv4.method shared

```

#### 3. 重启接口生效

配置改了必须重启接口才能启动 DHCP 服务。

```bash
nmcli connection down "Wired connection 1"
nmcli connection up "Wired connection 1"

```

#### 4. 验证本机 IP (网关)

确认你的 Ubuntu 网口是否变成了网关 IP（通常是 `10.42.0.1`）。

```bash
ifconfig enp45s0
# 或者
ip addr show enp45s0

```

#### 5. 扫描树莓派 IP

扫描 `10.42.0.x` 网段，寻找除了 `.1` 以外的设备。

```bash
sudo nmap -sn 10.42.0.0/24

```

* *如果没装 nmap，可以用 `arp -n` 或者查看 DHCP 租约：*
```bash
cat /var/lib/misc/dnsmasq.leases

```



#### 6. SSH 连接

拿到 IP（比如 `10.42.0.75`）后，直接登录。

```bash
ssh pollen@10.42.0.75

```

---

### 💡 两个重要的小贴士

1. **永久生效**：
这个配置是**永久的**。下次你把树莓派拔了，过几天再插上，只要还是插在这个网口，Ubuntu 会自动识别并再次启动共享模式，不需要重新敲命令。
2. **如果想恢复成普通网口**：
如果你以后要把这个网口插到墙上的路由器上网，记得把模式改回“自动”：
```bash
nmcli connection modify "Wired connection 1" ipv4.method auto
nmcli connection up "Wired connection 1"

```






pollen@reachy-mini:~ $ cat /boot/firmware/cmdline.txt.bak
console=serial0,115200 console=tty1 root=PARTUUID=28912d7b-02 rootfstype=ext4 fsck.repair=yes rootwait cfg80211.ieee80211_regdom=US
pollen@reachy-mini:~ $ 





pollen@reachy-mini:~ $ sudo nmcli device wifi connect "null" password "12345678"
Device 'wlan0' successfully activated with '89ecd360-5be4-4aa2-9ff0-e684f88991a6'.
pollen@reachy-mini:~ $ nmcli connection show
NAME                   UUID                                  TYPE      DEVICE 
Wired connection 2     c18fca69-808d-3d92-81bf-336f0da4534b  ethernet  eth1   
null                   89ecd360-5be4-4aa2-9ff0-e684f88991a6  wifi      wlan0  
lo                     bfb2ef45-494e-4d5f-a891-c29aa1649823  loopback  lo     
AX3000                 34d55700-cee1-4b8b-8151-e9d097cd43d3  wifi      --     
Hotspot                3b1f593d-0ff0-4139-9227-134c92c4f533  wifi      --     
OPPO Find X9 Pro 7DFE  fa209341-f840-461e-b9ca-5fba1ed39774  wifi      --     
SEEED-MKT              4a9a85ca-441c-42ff-bd9e-a21e49c83122  wifi      --     
TP-LINK_19D8           fae12e87-fb0b-4fc6-b3e1-11281df29b14  wifi      --     
Wired connection 1     fabb2596-9c31-3419-ad22-42e2f412d86e  ethernet  --     
omg                    a1b443e4-fd87-48af-a704-5c8b06683587  wifi      --     
softearth5             3eae759e-b27b-465c-9eda-cfe17f7a4ae8  wifi      --     
youjiangiPhone         4fdd687d-1959-4d98-af1a-139d75abdba3  wifi      --     
pollen@reachy-mini:~ $ ifconfig
eth0: flags=4099<UP,BROADCAST,MULTICAST>  mtu 1500
        ether 2c:cf:67:f8:b7:43  txqueuelen 1000  (Ethernet)
        RX packets 0  bytes 0 (0.0 B)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 0  bytes 0 (0.0 B)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

eth1: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 10.42.0.75  netmask 255.255.255.0  broadcast 10.42.0.255
        inet6 fe80::7397:3b93:8618:d4e1  prefixlen 64  scopeid 0x20<link>
        ether 6c:1f:f7:24:1f:fd  txqueuelen 1000  (Ethernet)
        RX packets 2172  bytes 165745 (161.8 KiB)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 868  bytes 221747 (216.5 KiB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

lo: flags=73<UP,LOOPBACK,RUNNING>  mtu 65536
        inet 127.0.0.1  netmask 255.0.0.0
        inet6 ::1  prefixlen 128  scopeid 0x10<host>
        loop  txqueuelen 1000  (Local Loopback)
        RX packets 96  bytes 9179 (8.9 KiB)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 96  bytes 9179 (8.9 KiB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

wlan0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 10.57.101.85  netmask 255.255.255.0  broadcast 10.57.101.255
        inet6 fe80::303d:7f29:a09e:f91e  prefixlen 64  scopeid 0x20<link>
        ether 2c:cf:67:f8:b7:44  txqueuelen 1000  (Ethernet)
        RX packets 57390  bytes 11784905 (11.2 MiB)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 223  bytes 32645 (31.8 KiB)
        TX errors 0  dropped 16 overruns 0  carrier 0  collisions 0

pollen@reachy-mini:~ $ 


确保自动连接

pollen@reachy-mini:~ $ nmcli connection show "null" | grep autoconnect
connection.autoconnect:                 yes
connection.autoconnect-priority:        0
connection.autoconnect-retries:         -1 (default)
connection.autoconnect-slaves:          -1 (default)
connection.autoconnect-ports:           -1 (default)
pollen@reachy-mini:~ $ 


