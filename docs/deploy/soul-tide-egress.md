# soul: Tide-only outbound firewall exception

Approved scope: only Tide's Docker bridge may make DNS and HTTPS connections,
with corresponding return traffic. No app/database ingress, other bridges, global
forward policy, Docker-generated iptables tables or host input rules change.

Observed topology: `geneticgrid_default`, ID prefix `07baec6b2e49`, bridge
`br-07baec6b2e49`, subnet `172.18.0.0/16`, uplink `eth0`. DNS servers from the
host resolver: `183.60.83.19`, `183.60.82.98`. Abort and reassess if these change.
The host's `inet filter forward` chain has drop policy; Docker's own forwarding
and NAT rules stay intact. Rule file is IPv4 only, matching the actual network.

## Install (after validation and repository push)

1. Confirm topology and that no `tide-egress-` rules exist.
2. Run `sudo nft -c -f docs/deploy/soul-tide-egress.nft` (check only).
3. Back up `/etc/nftables.conf`, then install the file as
   `/etc/nftables.d/tide-egress.nft` root-owned mode 0644.
4. Append exactly `include "/etc/nftables.d/tide-egress.nft"` to the END of
   `/etc/nftables.conf`, after its existing `inet filter` table definition.
   Check the complete file with `sudo nft -c -f /etc/nftables.conf`.
5. Apply ONLY the fragment with `sudo nft -f /etc/nftables.d/tide-egress.nft`.
   Do not reload the full firewall or flush any tables. The include persists
   the exception on the existing enabled nftables service's next boot.
6. Verify the six tagged rules, loopback-only ports, container DNS and public
   read-only market request. Check traffic counters, without trading credentials.

## Rollback

Remove only rules in `inet filter forward` whose comments begin `tide-egress-`:
list with `sudo nft -a list chain inet filter forward`, then for each matching
handle run `sudo nft delete rule inet filter forward handle HANDLE`.
Remove the one exact include line from `/etc/nftables.conf`; check the file with
`nft -c` before saving. The unused fragment can remain as an audit artifact.
Do not flush chains, delete Docker tables or restore a full snapshot over newer
unrelated firewall edits. Confirm the existing forward policy is still drop.
If rolling back the application to a build without public-mode protection, first
remove the public Caddy route. No credentials are included in these files.
