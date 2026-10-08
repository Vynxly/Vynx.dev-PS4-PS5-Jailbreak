# Changelog

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
