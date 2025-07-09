// Browser positioning and communication functions
function getOffsetSum(elem) {
    var top = 0, left = 0;
    while (elem) {
        top = top + parseInt(elem.offsetTop);
        left = left + parseInt(elem.offsetLeft);
        elem = elem.offsetParent;
    }
    return { top: top, left: left };
}

function getOffsetRect(elem) {
    var box = elem.getBoundingClientRect();
    var body = document.body;
    var docElem = document.documentElement;
    var scrollTop = window.pageYOffset || docElem.scrollTop || body.scrollTop;
    var scrollLeft = window.pageXOffset || docElem.scrollLeft || body.scrollLeft;
    var clientTop = docElem.clientTop || body.clientTop || 0;
    var clientLeft = docElem.clientLeft || body.clientLeft || 0;
    var top = box.top + scrollTop - clientTop;
    var left = box.left + scrollLeft - clientLeft;
    return { top: Math.round(top), left: Math.round(left) };
}

function getOffset(elem) {
    if (elem.getBoundingClientRect) {
        return getOffsetRect(elem);
    } else {
        return getOffsetSum(elem);
    }
}

function init(elem) {
    var bounds = null;
    if (elem != null) {
        bounds = elem.getBoundingClientRect();
    }
    
    var xmlHttp = new XMLHttpRequest();
    var w = Math.max(document.documentElement.clientWidth, window.innerWidth || 0);
    var h = Math.max(document.documentElement.clientHeight, window.innerHeight || 0);
    var winLeft = window.screenLeft ? window.screenLeft : window.screenX;
    var winTop = window.screenTop ? window.screenTop : window.screenY;
    var windowWidth = window.outerWidth;
    var windowHeight = window.outerHeight;
    
    var url = window.location.href + "&do=loaded&x=" + winLeft + "&y=" + winTop + 
              "&w=" + windowWidth + "&h=" + windowHeight + "&vw=" + w + "&vh=" + h;
    
    if (bounds) {
        url += "&eleft=" + bounds.left + "&etop=" + bounds.top + 
               "&ew=" + bounds.width + "&eh=" + bounds.height;
    }
    
    xmlHttp.open("GET", url, true);
    xmlHttp.send();
}

function unload() {
    try {
        var xhr = new XMLHttpRequest();
        xhr.open("GET", window.location.href + "&do=unload", true);
        xhr.timeout = 5000;
        xhr.send();
    } catch (err) {
        // Ignore errors
    }
}

function closeWindowOrTab() {
    if (window.location.hash) return;
    
    console.log("Close browser");
    
    // Try different methods to close the window/tab
    try {
        window.open('', '_self', '');
        window.close();
    } catch (e) {
        try {
            this.focus();
            self.opener = this;
            self.close();
        } catch (e2) {
            // Last resort - just hide the content
            document.body.innerHTML = '<h2>You can close this window now</h2>';
        }
    }
}

function refresh() {
    try {
        var xhr = new XMLHttpRequest();
        xhr.onTimeout = closeWindowOrTab;
        xhr.onerror = closeWindowOrTab;
        
        xhr.onLoad = function() {
            if (xhr.status == 0) {
                closeWindowOrTab();
            } else if (xhr.responseText == "true") {
                closeWindowOrTab();
            } else {
                setTimeout(refresh, 1000);
            }
        };
        
        xhr.onreadystatechange = function() {
            if (xhr.readyState == 4) {
                xhr.onLoad();
            }
        };
        
        xhr.open("GET", window.location.href + "&do=canClose", true);
        xhr.timeout = 5000;
        xhr.send();
    } catch (err) {
        closeWindowOrTab();
    }
}

// Initialize when page loads
window.addEventListener('load', function() {
    init(document.querySelector('.cf-turnstile') || document.querySelector('.g-recaptcha') || document.querySelector('.h-captcha'));
    setTimeout(refresh, 1000);
    
    // Check if Turnstile loaded successfully after a delay
    setTimeout(function() {
        var turnstileWidget = document.querySelector('.cf-turnstile');
        if (turnstileWidget && !turnstileWidget.innerHTML.trim()) {
            console.warn('Turnstile widget appears empty - may indicate site key issue');
            document.getElementById('error-info').style.display = 'block';
        }
    }, 3000);
});

// Handle page unload
window.addEventListener("beforeunload", unload);
