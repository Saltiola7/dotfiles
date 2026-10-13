# Planned Flint household gateway

Status: declared target only, not purchased or deployed. Owner: personal homelab
operator. Exact Flint model, firmware, LAN subnet and addressing are undecided.
This plan assigns network responsibilities; it does not move workloads or apply
configuration. Private addressing and credentials remain in local inventory.

## Target boundary

Initial topology: provider Huawei gateway connects to Flint WAN; Flint runs in
router mode with its own separate household LAN. Flint owns household DHCP, DNS
forwarding and firewall policy. Pi400, administration workstations and household
clients connect downstream. Parallels/Lima hosting and current containers retain
existing owners and locations. Only guests actually bridged onto household LAN
receive Flint leases; NAT guests retain their host-managed networks.

The provider gateway initially retains upstream routing, provider WAN, voice,
IPTV and any provider-managed service. This creates double NAT for household IPv4.
A provider bridge configuration is a later, separately approved option, not a
prerequisite for the initial deployment. Flint WAN still needs a working upstream
lease or separately verified addressing; adding Flint does not repair upstream
DHCP by itself. Do not blindly expand the provider pool or guess a static address.

Reuse the Huawei extender as a wired downstream access point only after confirming
standalone operation behind Flint. Its existing provider pairing may prevent this;
if incompatible, retain it temporarily on the old network and record that boundary,
or select a separate compatible access point later. No purchase is authorized.
There must be only one household DHCP authority on Flint LAN. Prevent provider
DHCP from reaching that LAN; an access point must not run a competing DHCP server.

## Cutover and rollback

1. Identify the purchased model and verify its documented capabilities/firmware.
   Choose a household subnet that does not overlap provider LAN, VPN routes or
   relevant VM networks. Record private bindings locally.
2. Preserve the provider configuration and current working administration path.
   Save available configuration backups privately. Prepare local recovery access.
3. Configure Flint through a local isolated connection using vendor-supported
   controls. The owner enters credentials privately. Enable its DHCP/DNS/firewall;
   do not expose management or SSH to the public WAN. Decide IPv6 behavior from
   observed provider prefix delegation; do not claim IPv6 support before testing.
4. Test Flint WAN connectivity, then a single downstream test client before moving
   the Pi or administration workstation. Obtain fresh interruption approval before
   any change that can disconnect the remote session.
5. Validate downstream DHCP server and lease, route, DNS, IPv4/IPv6 where available,
   internet, Tailscale and trusted SSH. Check extender operation, guest network
   behavior and capacity. No port forwarding or workload relocation is implied.
6. Move remaining household clients in a controlled sequence. Keep provider-specific
   equipment on its existing path unless separately understood and approved.
7. If validation fails, reconnect moved clients/extender to the prior working
   provider network and verify original DHCP and remote access. Preserve both
   configurations; do not factory-reset as routine rollback.
8. Mark planned edges observed only after verification, retain dated old observations,
   and update topology and private bindings together.

## Maintenance and acceptance

Before firmware upgrades or network-policy changes, export configuration backups
when supported, record rollback instructions and obtain interruption approval.
Review capacity, unexpected lease churn, software support and restore readiness.
Physical routers use configuration backups; VM snapshots do not protect their state.

Acceptance: household leases originate from Flint, provider leases remain upstream,
remote administration survives verified reconnection, and router/extender/guest
relationships are recorded accurately. Until then, all Flint edges remain planned.
The existing topology diagram and inventory are canonical; this document supplies
migration ordering and responsibilities without asserting deployment.

## Visual Evidence

Boundary, data/trust and dependency/deployment: required, represented by the
canonical topology diagram and Text Equivalent in [README](README.md#visual-evidence).
Current provider links are observed; future Flint links are planned. Operator owns
this evidence and updates both documents when cutover changes relationships.
Interaction: not_applicable to a new diagram; the numbered cutover procedure
explicitly defines ordering and approval handoffs. State: not_applicable to a new
visual; planned becomes observed only after acceptance checks above. Schema:
not_applicable; existing inventory schema is unchanged. Quantitative:
not_applicable; no measured Flint capacity or performance is claimed.
