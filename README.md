# Vynx Jailbreak WebKit

A simple local PS4 / PS5 WebKit host with **User Guide redirect** and **PSN/update blocking** built in.

## Requirements

- Windows PC
- Python 3
- PC and PlayStation connected to the same network

If Python is not installed, download it from:

<https://www.python.org/downloads/>

## How to use

1. Download and extract the latest release.
2. Double-click `.START-HOST.bat`.
3. The launcher will briefly show **Starting...** while the local DNS and web servers are being prepared.
4. When it shows **READY**, note the DNS address displayed.
5. On your PS4 / PS5, set **both Primary DNS and Secondary DNS** to that address.
6. Open **Settings -> User's Guide**.

Example:

```text
============================================
       Vynx.dev Jailbreak - READY
============================================

Set your PS4 / PS5 DNS to:

             192.168.1.100

Then open:
Settings -> User's Guide

Keep this window open.
Press CTRL+C to stop.
============================================
```

Keep the host window open while using the console.

### Why use the same DNS twice?

The PC is the only DNS server needed. Using the same address for both DNS fields prevents the console from falling back to a public DNS server and bypassing the local User Guide redirect or update blocking.

Do **not** use a public Secondary DNS such as `8.8.8.8` or `1.1.1.1`.

## PS5

If the User Guide shows a certificate warning, accept it to continue to the local host.

## PSN / update blocking

While your console is using the local DNS, the host blocks PlayStation/Sony network domains used by PSN and system/update services while still allowing the User Guide redirect to your local WebKit.

For extra protection, also disable automatic system and game updates in the console settings.

DNS blocking is an additional safeguard and should not be treated as an absolute guarantee against every possible update path or an already-cached connection.

## Direct browser access

You can also open the host directly from a browser using:

```text
http://YOUR-PC-IP/
```

Example:

```text
http://192.168.1.100/
```

## Troubleshooting

- Make sure the PC and console are on the same network.
- Allow Python through Windows Firewall for **Private networks** if prompted.
- Keep `.START-HOST.bat` open while the console is using the local DNS.
- If the host cannot start, right-click `.START-HOST.bat` and choose **Run as administrator**.
- If the wrong local IP is detected, run:

```cmd
py -3 local_host.py --ip YOUR-PC-IP
```

### Advanced / debugging

Normal DNS and web request logs are hidden to keep the launcher clean.

To show request logs:

```cmd
py -3 local_host.py --verbose
```

To temporarily disable PSN blocking for testing:

```cmd
py -3 local_host.py --allow-psn
```

---

**Vynx Developments**  
<https://vynx.dev>
