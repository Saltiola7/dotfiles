# Household DHCP incident and recovery

Date: 2026-10-12, America/Mexico_City. Owner: personal homelab operator.
This is an evidence record, not an automated router configuration procedure.
Private addresses, MACs, account identities and connection material remain local.

## Impact and evidence

The headless Pi400 booted correctly from its USB system SSD but did not receive
an IPv4 DHCP lease. IPv6 and trusted SSH worked, allowing diagnosis without a
monitor. Some IPv4-only package mirrors failed while IPv6-capable sources worked.

The Huawei HG8245H pool had capacity for 253 leases. Its UI initially reported
more allocations than capacity and a negative free count. Many unfamiliar phone
records were offline on SSID4. One sampled client had been offline for over
70 hours and still retained lease time under the three-day lease policy.
These are historical lease records, not proof that hundreds of clients were
simultaneously connected or that the network was compromised.

The Huawei WA8021V5-10 was a wired repeater, with seven reported terminals and
customer-visible household networks on both bands. Customer-visible configuration
did not establish who owned SSID4 or whether it belonged to Totalplay Club.

A 55-second DHCP capture on Pi during connection renewal recorded five outbound
Discover packets, no replies and zero kernel packet drops. Therefore no Offer
reached Pi during that capture. This does not prove the router received the
requests or establish the internal allocator failure.

## Changes, recovery and limits

1. The owner confirmed removal of two specifically inspected offline SSID4
   client records through the supported router UI. Displayed free capacity rose
   to one, but Pi still received no lease. UI cleanup alone did not prove allocator
   recovery. Do not bulk-delete unknown records or active clients.
2. With explicit interruption approval, changed DHCP lease duration from three
   days to six hours and renewed Pi Ethernet. Pool, subnet, DNS, relay, Option125,
   Wi-Fi and provider WAN services were preserved. Existing leases were not
   immediately shortened by changing the future lease duration.
3. The owner approved a normal router restart. Automation clicked Restart but
   encountered an inaccessible confirmation. Later the router showed login,
   without the confirmation. Whether restart completed remains unverified;
   no repeated restart was performed after connectivity recovered.
4. Trusted Pi inspection verified an IPv4 DHCP address, default gateway, DNS and
   DHCP server from the Huawei, with a 21,600-second lease. IPv4 HTTPS returned
   HTTP 200; SSH and Tailscale remained active. Pi did not reboot during recovery.
5. The owner supplied a refreshed router table: 253 capacity, nine Ethernet and
   two Wi-Fi leases, 242 free, and Pi400 listed correctly. All shown lease times
   were close to six hours, consistent with recently acquired leases.

**Conclusion:** IPv4 DHCP service and pool capacity recovered. Stale allocations
and long retention were observed. A lease-table reset is suggested by the new
clustered lease lifetimes, but the exact clearing event and original cause remain
unconfirmed. Totalplay Club involvement, provider isolation failure, and compromise
are unproven. Six-hour leases mitigate retention; they do not guarantee that
high client churn or provider behavior cannot exhaust this pool again.

## Repeatable diagnosis and recovery

- Preserve working remote access. Compare DHCP capacity with live clients and
  historical leases; inspect the extender separately.
- Use verified host-key SSH over Tailscale or IPv6. Check interface addresses,
  default routes and NetworkManager DHCP options before changing anything.
- If privileged capture is needed, the owner enters sudo privately. Capture
  DHCP on Pi while renewing only its Ethernet profile; a switched-LAN capture
  on another host may miss unicast replies and does not establish Pi behavior.
- Request approval before router Apply, connection renewal or restart that could
  interrupt remote access. Ensure local recovery is possible before restarting.
- Use supported normal Restart only if still needed; never factory-reset or
  alter provider WAN, IPTV, voice, relay or Wi-Fi based on this record.
- Verify DHCP server, lease, route, DNS, IPv4 internet and remote access afterward.
  Compare the refreshed router table; a successful UI click is not recovery proof.
- If capacity refills, record lease/client trends and ask the provider to clarify
  SSID4/Club isolation. Do not infer compromise from history alone.

## Retention and review

Keep raw captures and private connection details out of Git. Preserve this record
when migrating to Flint; append new evidence rather than rewriting uncertainty.
Review on recurrence and during the future gateway cutover. The current network
continues to rely on the provider gateway until that cutover is verified.

## Visual Evidence

Boundary, interaction, state, data/trust, schema and dependency/deployment:
not_applicable to additional visuals; this incident record uses an ordered evidence
narrative and points to the canonical topology for unchanged system boundaries.
Quantitative: not_applicable to a chart; capacity and capture counts are diagnostic
observations from one incident, not a trend or performance comparison.
