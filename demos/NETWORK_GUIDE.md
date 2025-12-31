# Reachy Mini Network Connection Configuration Guide

Standard Operating Procedure (SOP) for implementing network sharing via command line (CLI) on Ubuntu.

---

## Scenario Description

**Connection Method:**
```
Raspberry Pi <---> Hub(USB to Ethernet) <---> Ethernet Cable <---> Ubuntu PC Ethernet Port (enp45s0)
```

**Goal**: Ubuntu PC connects to internet via Wi-Fi and shares network to Ethernet port, allowing Raspberry Pi to get IP (`10.42.0.x`) and access internet.

---

## Table of Contents

1. [Quick Configuration Steps](#quick-configuration-steps)
2. [Verification and Connection](#verification-and-connection)
3. [Important Notes](#important-notes)
4. [Reference Information](#reference-information)

---

## Quick Configuration Steps

### Step 1: Confirm Interface Name and Connection Name

First check the network card name and corresponding connection name (NAME).

```bash
nmcli device
```

**Goal**: Find the row where `TYPE` is `ethernet`.

**Assumed result**: DEVICE is `enp45s0`, CONNECTION is `Wired connection 1`.

---

### Step 2: Enable "Shared" Mode (Key Step)

Change the IPv4 method of the wired connection to `shared` (equivalent to "Allow other users to connect through this computer" in Windows).

```bash
nmcli connection modify "Wired connection 1" ipv4.method shared
```

---

### Step 3: Restart Interface for Changes to Take Effect

After configuration changes, you must restart the interface to start the DHCP service.

```bash
nmcli connection down "Wired connection 1"
nmcli connection up "Wired connection 1"
```

---

### Step 4: Verify Local IP (Gateway)

Confirm that the Ubuntu Ethernet port has become the gateway IP (usually `10.42.0.1`).

```bash
ifconfig enp45s0
# or
ip addr show enp45s0
```

---

## Verification and Connection

### Step 5: Scan for Raspberry Pi IP

Scan the `10.42.0.x` subnet to find devices other than `.1`.

```bash
sudo nmap -sn 10.42.0.0/24
```

**If nmap is not installed**, you can use these alternatives:

```bash
# Method 1: Use arp
arp -n

# Method 2: View DHCP leases
cat /var/lib/misc/dnsmasq.leases
```

---

### Step 6: SSH Connection

Once you have the IP (e.g., `10.42.0.75`), log in directly.

```bash
ssh pollen@10.42.0.75
```

---

## Important Notes

### Permanent Effect

This configuration is **permanent**. Next time you unplug the Raspberry Pi and plug it back in days later, as long as it's plugged into the same Ethernet port, Ubuntu will automatically recognize and start shared mode again without needing to re-enter commands.

### Restore Normal Ethernet Mode

If you later want to plug this Ethernet port into a wall router for internet, remember to change the mode back to "auto":

```bash
nmcli connection modify "Wired connection 1" ipv4.method auto
nmcli connection up "Wired connection 1"
```

---

## Reference Information

### Example Network Configuration

**Raspberry Pi network status example:**

```
eth1: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 10.42.0.75  netmask 255.255.255.0  broadcast 10.42.0.255
        ether 6c:1f:f7:24:1f:fd  txqueuelen 1000  (Ethernet)
```

**WiFi connection status:**

```
wlan0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 10.57.101.85  netmask 255.255.255.0  broadcast 10.57.101.255
        ether 2c:cf:67:f8:b7:44  txqueuelen 1000  (Ethernet)
```

### WiFi Auto-connection Settings

Ensure WiFi is configured for auto-connection:

```bash
# Check auto-connection settings
nmcli connection show "YOUR_WIFI_SSID" | grep autoconnect

# Output should be:
# connection.autoconnect:                 yes
```

### WiFi Connection Commands

```bash
# Connect to WiFi
sudo nmcli device wifi connect "SSID_NAME" password "PASSWORD"

# View all connections
nmcli connection show
```

---

## FAQ

### Q: Can't find Raspberry Pi IP?

A: Confirm the following:
1. Ethernet cable is plugged in properly
2. Ubuntu shared mode is enabled
3. Raspberry Pi is powered on
4. Use `arp -n` or check DHCP leases

### Q: SSH connection fails?

A: Check:
1. IP address is correct
2. Raspberry Pi SSH service is running
3. Firewall is not blocking connection

### Q: Raspberry Pi can't access internet after network sharing?

A: Check:
1. Ubuntu PC is connected to internet
2. Ubuntu firewall/NAT settings
3. DNS resolution is working
