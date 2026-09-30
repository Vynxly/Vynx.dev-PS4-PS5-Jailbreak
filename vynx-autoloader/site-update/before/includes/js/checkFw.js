function isLocalIP(ip) {
    return /^(127\.|192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[0-1])\.)/.test(ip);
}

function getPs4FwVersion(ua) {
    if (!ua) return "";
    var match = ua.match(/PlayStation 4[\/\s]+([\d.]+)/i);
    return match ? match[1] : "";
}

var ps5RelapseSupportedFirmware = [
    "13.60", "13.42", "13.40", "13.20", "13.00",
    "12.70", "12.60", "12.40", "12.20", "12.02", "12.00",
    "11.60", "11.20", "11.00",
    "10.60", "10.40", "10.20", "10.01", "10.00",
    "9.60", "9.40", "9.20", "9.00",
    "8.60", "8.40", "8.20", "8.00",
    "7.61", "7.60", "7.40", "7.20", "7.01", "7.00"
];

function getPs5FwVersion(ua) {
    if (!ua) return "";
    var match = ua.match(/PlayStation 5[\/\s]+([\d.]+)/i);
    return match ? match[1] : "";
}

function isPs5RelapseSupportedFirmware(fwVersion) {
    return ps5RelapseSupportedFirmware.indexOf(String(fwVersion || "")) !== -1;
}

// Hide GoldHEN radio when its unsupported
function updateHenFlavorVisibility(fwVersion) {
    var fwNum = parseFloat(fwVersion);
    var hideGoldHEN = (fwNum > 13.00 && fwNum !== 13.52) ? true : false;
    if (isNaN(fwNum)) return;

    const goldHenInputInitial = document.getElementById('goldhen-label-initial');
    const goldHenInputExploit = document.getElementById('goldhen-label-exploit');
    const goldHenVersionSelector = document.getElementById('chooseGoldHEN');

    if (hideGoldHEN) {
        if (goldHenInputInitial && goldHenInputExploit && goldHenVersionSelector){
            goldHenInputInitial.classList.toggle('hidden', hideGoldHEN);
            goldHenInputExploit.classList.toggle('hidden', hideGoldHEN);
            goldHenVersionSelector.classList.toggle('hidden', hideGoldHEN);
        }
        var henInputs = document.querySelectorAll(
            'input[name="hen"][value="HEN"], input[name="hen2"][value="HEN"]'
        );
        henInputs.forEach(function (input) {
            input.checked = true;
        });
        user.currentJbFlavor = 'HEN';
        localStorage.setItem('jailbreakFlavor', 'HEN');
    }
}

function CheckFW() {
    var userAgent = navigator.userAgent;
    var ps4Regex = /PlayStation 4/;
    var ps5Regex = /PlayStation 5/;
    var fwVersion = getPs4FwVersion(userAgent);
    var ps5FwVersion = getPs5FwVersion(userAgent);
    var isLocalServer = isLocalIP(window.location.hostname) || window.location.hostname == "localhost";

    var elementsToHide = [
        'ps-logo-container', 'choosejb-initial', 'exploit-main-screen', 'scrollDown',
        'click-to-start-text', 'chooseGoldHEN', 'advancedPayloads', 'chooseExploitChain'
    ];

    if (ps4Regex.test(userAgent)) {
        window.ps4Fw = fwVersion;
        user.ip = "127.0.0.1";
        user.ps4Fw = fwVersion;

        var fwNum = parseFloat(fwVersion);
        // updateHenFlavorVisibility(fwVersion); // GoldHEN is now supported.
        if (fwNum >= webKitMin && fwNum <= webKitMax) {
            ui.ps4FwStatus.style.color = 'green';

            // Highlight firmware in about popup
            var dotIndex = fwVersion.indexOf('.');
            var major = dotIndex !== -1 ? fwVersion.substring(0, dotIndex) : fwVersion;
            var fwElement = "fw" + major;

            var el = document.getElementById(fwElement);
            if (el) el.classList.add('fwSelected');

            updateExploitChainVisibility(fwVersion);
            firstTimeExploitChain(fwVersion);
        } else {
            ui.ps4FwStatus.style.color = 'orange';
            document.getElementById('layouts').style.display = "none";
            document.getElementById('layout').style.display = "none";
            if (isHttps()) {
                if (ui.secondHostBtn && ui.secondHostBtn[0]) {
                    ui.secondHostBtn[0].style.display = "block";
                }
                try {
                    terminateCache(); // Dont cache in case no webkit and is https
                } catch (e) {
                    console.warn("terminateCache notice: " + e.message);
                }
            } else {
                var toRemove = ['exploit-main-screen', 'scrollDown', 'advancedPayloads'];
                elementsToHide = elementsToHide.filter(function (e) {
                    return toRemove.indexOf(e) === -1;
                });
                elementsToHide.push('initial-screen', 'exploit-status-panel', 'henSelection', 'autoJbContainer', 'successRate', 'bareboneJBOption', 'chooseExploitChain');
                if (fwNum < 6.70) elementsToHide.push('layouts', 'theme'); // Incompatible with Compact design..
                document.getElementById('exploitContainer').style.display = "block";

                // Sizing the payload's section
                ui.payloadsSection.style.margin = "auto";
                document.getElementById('header2').classList.remove('hidden');
            }

            elementsToHide.forEach(function (id) {
                var el = document.getElementById(id);
                if (el) el.style.display = 'none';
            });
        }
    } else if (ps5Regex.test(userAgent)) {
        window.ps5Fw = ps5FwVersion;
        user.platform = 'PS5';
        user.ps5Fw = ps5FwVersion;
        user.ip = "127.0.0.1";

        var supportedPs5 = isPs5RelapseSupportedFirmware(ps5FwVersion);
        ui.ps4FwStatus.style.color = supportedPs5 ? 'green' : 'orange';
        ui.ps4FwStatus.style.textAlign = "center";

        var subtitle = document.getElementById('vynx-brand-subtitle');
        if (subtitle) subtitle.textContent = 'PS5 JAILBREAK';

        // The PS5 Relapse chain has its own payload flow, so hide PS4-only controls.
        [
            'choosejb-initial', 'scrollDown', 'exploit-main-screen', 'chooseGoldHEN',
            'advancedPayloads', 'chooseExploitChain', 'autoJbContainer', 'reloadAfterJb',
            'updateCache'
        ].forEach(function (id) {
            var el = document.getElementById(id);
            if (el) el.style.display = 'none';
        });
    } else {
        // Not a supported PlayStation browser
        user.platform = 'Unknown platform';
        if (/Android/.test(userAgent)) user.platform = 'Android';
        else if (/iPhone|iPad|iPod/.test(userAgent)) user.platform = 'iOS';
        else if (/Macintosh/.test(userAgent)) user.platform = 'MacOS';
        else if (/Windows/.test(userAgent)) user.platform = 'Windows';
        else if (/Linux/.test(userAgent)) user.platform = 'Linux';

        // For user selected firmware
        if (user.ps4Fw) ui.ps4FwSelect.value = user.ps4Fw;
        // Show only if on a local server
        if (isLocalServer && !devMode) {
            // Show IP input and firmware selector for local server users on smart devices
            ui.ps4IpInput.classList.remove('hidden');
            ui.ps4FwSelect.classList.remove('hidden');
            ui.scanGoldHENPayLoader.classList.remove('hidden');
            ui.shutdownServerBtn.classList.remove('hidden');
            document.querySelector('.customPayloadsTab').classList.remove('hidden');
            ui.ps4IpInput.value = user.ip;

            var toRemove2 = ['exploit-main-screen', 'scrollDown', 'advancedPayloads', 'custom-tab'];
            elementsToHide = elementsToHide.filter(function (e) {
                return toRemove2.indexOf(e) === -1;
            });
            elementsToHide.push('initial-screen', 'henSelection', 'autoJbContainer', 'successRate', 'bareboneJBOption', 'chooseExploitChain', 'layouts', 'theme');

            // Sizing the payload's section
            // Full screen for phones, centered for desktop
            if (user.platform == "Android" || user.platform == "iOS") {
                // hide console
                elementsToHide.push('exploit-status-panel');
                document.getElementById('exploitContainer').style.display = "block";
                ui.exploitScreen.style.padding = "0";
                document.getElementById('layouts').style.display = "none";
                document.getElementById('layout').style.display = "none";
            }
            ui.payloadsSection.style.width = "100%";
            ui.payloadsSection.style.margin = "auto";
            // Moving the settings icon to a better place
            document.getElementById('header2').classList.remove('hidden', 'left-6');
            document.getElementById('header2').classList.add('flex', 'inherit');

            // add borders to buttons in header2
            var buttons = document.getElementById('header2').querySelectorAll('button');
            for (var i = 0; i < buttons.length; i++) {
                buttons[i].classList.add('border', 'border-white/20', 'rounded-xl');
            }
            // Hide elements for local server users unless in dev mode
            if (!devMode) {
                elementsToHide.forEach(function (id) {
                    var el = document.getElementById(id);
                    if (el) el.style.display = 'none';
                });
            }
        }
        ui.ps4FwStatus.style.color = 'red';
        ui.ps4FwStatus.style.textAlign = "center";
    }
}

function firstTimeExploitChain(fwVersion) {
    const currentExploitChain = localStorage.getItem('exploitChain');
    if (currentExploitChain != null && !isNaN(currentExploitChain)) return;
    var fwNum = parseFloat(fwVersion);
    var chain = 4; // Default to CSSFontFace Lapse
    if (fwNum >= 6.70 && fwNum <= 6.72) {
        chain = 2; // BadHoist
    }
    else if (fwNum >= 7.00 && fwNum <= 9.60) {
        chain = 1; // Bundle PSFree Lapse
    } else if (fwNum >= 11.50 && fwNum <= 12.02) {
        chain = 5; // SlopKit lapse
    } else if (fwNum >= 13.02 && fwNum <= 13.52) {
        chain = 7; // Relapse
    } else if (fwNum >= 12.50 && fwNum < 13.02) {
        chain = 6; // SlopKit Netctrl
    }
    if (typeof exploitChain === 'function') {
        exploitChain(chain);
    }
    if (typeof loadExploitChain === 'function') {
        loadExploitChain();
    }
}

function toggleVisibility(id, show) {
    var el = document.getElementById(id);
    if (!el) return;
    if (show) {
        el.classList.remove('hidden');
    } else {
        el.classList.add('hidden');
    }
}

function updateExploitChainVisibility(fwVersion) {
    if (!fwVersion) return;
    var fwNum = parseFloat(fwVersion);
    if (isNaN(fwNum)) return;

    // cssfontface lapse and netctrl 9.00 - 11.02
    var showCssFontFaceLapse = (fwNum >= 9.00 && fwNum <= 11.02);
    var showCssFontFaceNetctrl = (fwNum >= 9.00 && fwNum <= 11.02);
    toggleVisibility('cssFontFaceNetCtrlExp', showCssFontFaceNetctrl);
    toggleVisibility('cssFontFaceLapseExp', showCssFontFaceLapse);

    // 6.70 - 6.72 sees badhoist
    var showBadHoist = (fwNum >= 6.70 && fwNum <= 6.72);
    toggleVisibility('badHoistExp', showBadHoist);

    // 7.00 - 9.60 sees modular and bundled psfree lapse
    var showPsfreeLapse = (fwNum >= 7.00 && fwNum <= 9.60);
    toggleVisibility('modularLapseExp', showPsfreeLapse);
    toggleVisibility('bundleLapseExp', showPsfreeLapse);

    var showSlopKitLapse = (fwNum >= 11.00 && fwNum <= 12.02);
    var showSlopKitNetCtrl = (fwNum >= 12.50 && fwNum <= 13.00);
    toggleVisibility('slopKitLapseExp', showSlopKitLapse);
    toggleVisibility('slopKitNetCtrlExp', showSlopKitNetCtrl);

    var showRelapse = (fwNum >= 13.02 && fwNum <= 13.52);
    toggleVisibility('relapseExp', showRelapse);
}