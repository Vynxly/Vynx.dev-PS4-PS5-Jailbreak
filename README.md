# Vynx Jailbreak Webkit

A simple PS4 / PS5 WebKit exploit host that can be hosted directly from your PC on your local network.

## Local Hosting

### Requirements

- Windows PC
- Python 3
- Your PC and PlayStation connected to the same network

You can check whether Python is installed by opening Command Prompt and running:

```cmd
py -3 --version
```

If Python is not installed, download Python 3 from:

https://www.python.org/downloads/

Make sure Python is added to your PATH during installation.

## Starting the WebKit Host

1. Download or clone this repository.

2. Extract the files if necessary.

3. Double-click:

```text
.START-HOST.bat
```

4. A Command Prompt window will open and display an address similar to:

```text
http://192.168.1.100:8080
```

5. On your PS4 or PS5, open the web browser / User's Guide and navigate to the address shown.

For example:

```text
http://192.168.1.100:8080
```

Keep the Command Prompt window open while using the host.

To stop the server, press:

```text
CTRL+C
```

## Manual Hosting

If the included batch file does not work, open Command Prompt inside the WebKit folder and run:

```cmd
py -3 -m http.server 8080 --bind 0.0.0.0
```

Find your PC's local IP with:

```cmd
ipconfig
```

Look for your IPv4 address, then open the following on your PlayStation:

```text
http://YOUR-PC-IP:8080
```

Example:

```text
http://192.168.1.100:8080
```

## Troubleshooting

If the page does not load:

- Make sure the PC and PlayStation are on the same network.
- Allow Python through Windows Firewall if prompted.
- Make sure port `8080` is not being used by another program.
- Do not close the server window while using the WebKit.
- Use your PC's local IPv4 address, not `localhost` or `127.0.0.1`.

---

**Vynx Developments**  
https://vynx.dev
