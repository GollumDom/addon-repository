# Home Assistant Add-on: OpenThread Border Router

## Installation

Follow these steps to get the add-on installed on your system:

1. Navigate in your Home Assistant frontend to **Settings** -> **Add-ons, Backup & Supervisor** -> **Add-on Store**.
2. Click on the top right menu and "Repository"
3. Add "https://github.com/home-assistant/addons" to add the "Home Assistant Add-on Repository for Development" repository.
4. Find the "OpenThread Border Router" add-on and click it.
5. Click on the "INSTALL" button.

## How to use

You will need a 802.15.4 capable radio supported by OpenThread flashed with OpenThread
RCP firmware. Home Assistant Yellow as well as Home Assistant SkyConnect/Connect ZBT-1
are both able to run OpenThread and will be flashed with the correct firmware by Home
Assistant Core.

If you are using Home Assistant Yellow, choose `/dev/ttyAMA1` as device.

### Alternative radios

The website [openthread.io maintains a list of supported platforms][openthread-platforms]
lists other Thread capable radios. A well documented Radio for development is the
Nordic Semiconductor [nRF52840 Dongle][nordic-nrf52840-dongle]. The Dongle needs
a recent version of the OpenThread RCP firmware.
[This article][nordic-nrf52840-dongle-install] outlines the steps to install the
RCP firmware for the nRF52840 Dongle.

Once the firmware is loaded follow the following steps:

1. Select the correct `device` in the add-on configuration tab and press `Save`.
2. Start the add-on.

### OpenThread Border Router

This add-on makes your Home Assistant installation an OpenThread Border Router
(OTBR). The border router can be used to comission Matter devices which connect
through Thread. Home Assistant Core will automatically detect this add-on and
create a new integration named "Open Thread Border Router". With Home Assistant
Core 2023.3 and newer the OTBR will get configured automatically. The Thread
integration allows to inspect the network configuration.

### Web interface (advanced)

There is also a web interface provided by the OTBR. However, the web
interface has caveats (e.g. forming a network does not generate an off-mesh
routable IPv6 prefix which causes changing IPv6 addressing on first add-on
restart). It is still possible to enable the web interface for debugging
purpose. Make sure to expose both the Web UI port and REST API port (the
latter needs to be on port 8081) on the host interface. To do so, click on
"Show disabled ports" and enter a port (e.g. 8080) in the OpenThread Web UI
and 8081 in the OpenThread REST API port field).

## Configuration

Add-on configuration:

| Configuration      | Description                                            |
|--------------------|--------------------------------------------------------|
| device (mandatory) | Serial port where the OpenThread RCP Radio is attached |
| baudrate           | Serial port baudrate (depends on firmware)   |
| flow_control       | If hardware flow control should be enabled (depends on firmware) |
| otbr_log_level     | Set the log level of the OpenThread BorderRouter Agent     |
| firewall           | Enable OpenThread Border Router firewall to block unnecessary traffic |
| nat64              | Enable NAT64 to allow Thread devices accessing IPv4 addresses |
| network_device     | IP address and port to connect to a network-based RCP (see below) |

> [!WARNING]
> The OTBR expects the RCP connected radio to be on a reliable link such as
> UART or SPI. Using TCP/IP to reach a remote RCP radio breaks this assumption.
> If the TCP/IP connection fails, the OTBR will not shutdown cleanly and leave
> stale routes in your network. This will lead to Thread devices to be
> potentially unreachable for up to 30 minutes (route lifetime) even when other
> routers are available.
>
> The RCP protocol is not designed to be transferred over an IP network: It is
> a timing-sensitive protocol. You might experience Thread issues if your
> network link has excessive latencies. As Thread is networking capable,
> running a Thread border router on the system the RCP radio is plugged in is
> recommended.

> [!NOTE]
> When using a network device, you still need to set a dummy serial port device, e.g. `/dev/ttyS3`.

## Support

Got questions?

You have several options to get them answered:

- The [Home Assistant Discord Chat Server][discord].
- The Home Assistant [Community Forum][forum].
- Join the [Reddit subreddit][reddit] in [/r/homeassistant][reddit]

In case you've found a bug, please [open an issue on our GitHub][issue].

[discord]: https://discord.gg/c5DvZ4e
[forum]: https://community.home-assistant.io
[reddit]: https://reddit.com/r/homeassistant
[issue]: https://github.com/home-assistant/addons/issues
[openthread-platforms]: https://openthread.io/platforms
[nordic-nrf52840-dongle]: https://www.nordicsemi.com/Products/Development-hardware/nrf52840-dongle
[nordic-nrf52840-dongle-install]: https://docs.nordicsemi.com/bundle/ncs-latest/page/nrf/protocols/thread/tools.html#configuring_a_radio_co-processor

## Troubleshooting a network device (fork-specific)

This fork drives the RCP over TCP (`network_device`, e.g. an SLZB-06 in
"Thread to remote OTBR" mode). Two failure modes look identical in the log —
`Init() at spinel_driver.cpp:87: Failure`, followed by the container stopping —
but have different causes.

### `tiocmbic: Inappropriate ioctl for device`

Fixed in 3.1.0.2. The upstream add-on appends `uart-init-deassert` to the radio
URL when `flow_control` is off; `otbr-agent` then issues `ioctl(TIOCMBIC)` to
deassert DTR/RTS, which a socat PTY does not implement. Port setup gives up
before `tcsetattr`, so the baud rate is never applied. This fork now drops the
UART flow-control parameters whenever a `network_device` is configured — serial
flow control has no meaning over TCP. The log line to look for is:

```
INFO: Network device in use: dropping UART flow control parameters.
```

### No `tiocmbic`, still `spinel_driver.cpp:87`

Line 87 is `SuccessOrDie(CheckSpinelVersion())`: `otbr-agent` asked the RCP for
its spinel version and got no answer. If socat had failed to connect you would
see `hdlc_interface.cpp:154: No such file or directory` instead, so the TCP
session is fine — the radio itself is not talking.

A radio that has been up for a long time can freeze in a state where only a
**hardware reset** revives it. Over TCP there are no DTR/RTS lines, so neither
`otbr-agent` nor socat can toggle the reset pin; the adapter has to do it. On an
SLZB-06, use **Settings and Tools → General settings → Zigbee restart**, then
start the add-on again.

To confirm the diagnosis before touching anything, ask the RCP for its version
straight from the network — no add-on involved:

```python
import socket
def fcs16(d, f=0xffff):
    for b in d:
        f ^= b
        for _ in range(8):
            f = (f >> 1) ^ 0x8408 if f & 1 else f >> 1
    return f
def hdlc(p):
    f = fcs16(p) ^ 0xffff
    body = p + bytes([f & 0xff, (f >> 8) & 0xff])
    out = bytearray([0x7e])
    for b in body:
        out += bytes([0x7d, b ^ 0x20]) if b in (0x7e, 0x7d, 0x11, 0x13, 0xf8) else bytes([b])
    out.append(0x7e)
    return bytes(out)

s = socket.create_connection(("192.168.0.225", 6638), timeout=5)
s.settimeout(3)
s.sendall(hdlc(bytes([0x82, 0x02, 0x02])))   # GET SPINEL_PROP_NCP_VERSION
print(s.recv(4096))
```

A healthy RCP answers with something like
`OPENTHREAD/1.4.0.0; CC13XX_CC26XX thread-v1.4-ti-1.0-ea-1.0; SLZB-06P10 20260304`.
Silence means the radio needs its hardware reset.
