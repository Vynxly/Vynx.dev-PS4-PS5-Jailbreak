# Vynx Jailbreak WebKit

A simple local PS4 / PS5 WebKit host with **User Guide redirect** and **PSN/update blocking** built in.

## What you need

- Windows PC
- Python 3
- PC and PlayStation on the same network

Install Python from <https://www.python.org/downloads/> if you do not already have it.

## Start it

1. Extract the release.
2. Double-click `.START-HOST.bat`.
3. The window will show your PC's DNS address.
4. On your PS4 / PS5, set **both Primary DNS and Secondary DNS** to that address.
5. Open **Settings -> User's Guide**.

Example:

```text
Vynx.dev Jailbreak - READY

Set your PS4 / PS5 DNS to:

             192.168.1.100

Then open:
Settings -> User's Guide

Keep this window open.
Press CTRL+C to stop.
```

Keep the host window open while using the console.

### PS5

If the User Guide shows a certificate warning, accept it to continue to the local host.

## Update / PSN protection

While your console is using this PC as DNS, the host blocks PlayStation/Sony network domains used by PSN, system updates, title-update metadata, and telemetry. The local User Guide address is allowed and redirected back to your PC.

**Do not set a public Secondary DNS such as `8.8.8.8` or `1.1.1.1`.** That can bypass the local blocking if the console uses the secondary server.

For extra protection, also disable automatic system/game update downloads in the console settings. DNS blocking is a strong additional safeguard, but it should not be treated as an absolute guarantee against every possible update path or cached connection.

## Direct browser access

You can also open the host directly at:

```text
http://YOUR-PC-IP/
```

## Troubleshooting

- Allow Python through Windows Firewall for **Private networks** if prompted.
- Keep `.START-HOST.bat` open while the console is using this DNS.
- If the host cannot start, right-click `.START-HOST.bat` and choose **Run as administrator**.
- If your PC has multiple network adapters and the wrong address is detected, run:

```cmd
py -3 local_host.py --ip YOUR-PC-IP
```

### Advanced / debugging

Normal request logs are hidden to keep the launcher clean. To show DNS and web requests:

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
