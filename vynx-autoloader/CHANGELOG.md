# Changelog

## 2.2 - 2026-11-20

- Route supported PS5 firmware automatically: keep UMTX2 for firmware 1.00–5.50 and use the upstream Wobkot runtime for firmware 6.00–13.60.
- Let Wobkot select Relapse or Poops based on firmware and network state, matching the linked upstream pre-release.
- Use Payload Manager v0.6.3 in both the first-install handoff and Relapse optional-payload flow (SHA-256 `2a42054fd9725e1d9595ff4add95abc30e5b49446fcdcb96c06775a376a841c4`). Refresh the offline cache with the new runtime.
- Credit ufm42's Wobkot and itsPLK's v0.8.0-pre autoloader integration.

## 2.1 - 2026-10-08

- Backport the experimental Poops racer-termination fix from srbraboo's v0.5.2-kp-fix. Termination runs only after stage 3 certifies alias repair; descriptors remain parked until reboot.
- Verify worker exit statuses. Failed or timed-out termination remains in diagnostics and prevents the automatic payload handoff from reporting success.
- Match upstream's already-jailbroken behavior on the automatic Poops path: report that elfldr is already running rather than send the bootstrap payload again.
- Backport upstream Relapse stability changes from the remote-loader revision used by itsPLK's v0.6.1: a 1000 ms settling delay after parking AIO workers, 100 ms between AIO cleanup entries, and nonblocking kernel-access pipes.
- Retain the already-integrated Poops offset fixes for firmware 9.05, 11.40, and 11.60.
- Retain firmware 1.00-5.50 support and the Vynx installer/runtime. This is a selective backport, not a migration to upstream's new v0.6 architecture.
- Use a new versioned offline cache directory. Existing installations need the new installer run once.

The Poops KP fix applies when the Poops chain runs. Relapse remains the default on firmware supported by both chains; firmware 9.05 and 11.40 use Poops. Relapse receives its separate upstream stability improvements.

Offline tests validate cleanup guards, failure handling, pipe flags, timing, and bundled source consistency. They cannot establish console success rates or guarantee elimination of kernel panics.

- Update the first-install Payload Manager handoff to user-provided v0.6.3 (SHA-256 `2a42054fd9725e1d9595ff4add95abc30e5b49446fcdcb96c06775a376a841c4`).
- Update the Relapse-side optional Payload Manager asset and loader reference to v0.6.3.
