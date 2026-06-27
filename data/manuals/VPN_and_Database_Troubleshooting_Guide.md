# VPN Troubleshooting Guide

## Common Issue: VPN Authentication Failure After Password Reset

When a user resets their domain password, the VPN client may continue to use
cached credentials, resulting in repeated authentication failures.

### Resolution Steps
1. Close the VPN client completely (ensure it is not running in the background).
2. Clear the cached credentials:
   - Windows: Open Credential Manager and remove entries related to the VPN profile.
   - macOS: Open Keychain Access and delete the saved VPN password entry.
3. Restart the VPN client.
4. Reconnect using the new password.
5. If the issue persists, verify the account is not locked in Active Directory.

## Common Issue: VPN Connection Timeout

Connection timeouts are frequently caused by network congestion or an outdated
VPN client version.

### Resolution Steps
1. Verify internet connectivity outside the VPN.
2. Update the VPN client to the latest version.
3. Switch from UDP to TCP transport in the VPN client settings if timeouts persist.
4. Check split-tunnel configuration to ensure only required traffic routes through VPN.

## Common Issue: Random Disconnections

Idle timeout settings can cause the VPN to disconnect after a period of inactivity.

### Resolution Steps
1. Open VPN client settings and disable or extend the idle timeout.
2. Ensure the client is updated to the latest version, as older versions have a
   known keep-alive bug.
3. Check for network adapter power-saving settings that may be disconnecting
   the connection.

---

# Database Service Troubleshooting Guide

## Common Issue: Connection Refused

This typically indicates the database service is not running or is not
accepting connections from the application server's IP address.

### Resolution Steps
1. Check if the PostgreSQL service is running: `systemctl status postgresql`.
2. Restart the service if needed: `systemctl restart postgresql`.
3. Verify `pg_hba.conf` includes an entry allowing connections from the
   application server's IP range.
4. Confirm the `listen_addresses` setting in `postgresql.conf` is not
   restricted to localhost only.

## Common Issue: Slow Query Performance

Slow queries are often caused by missing indexes or outdated table statistics.

### Resolution Steps
1. Use `EXPLAIN ANALYZE` to identify the slow part of the query plan.
2. Add an index on frequently filtered or joined columns.
3. Run `ANALYZE` on the affected table to refresh planner statistics.
4. Consider a read replica for heavy reporting workloads.
