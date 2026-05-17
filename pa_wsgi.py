"""
PythonAnywhere WSGI 入口 — 自动启动 Streamlit 并反向代理

将文件内容中的 your-username 替换为你的 PythonAnywhere 用户名，
然后在 Web 面板中将此文件设置为 WSGI configuration file。
"""
import os
import sys
import subprocess
import time
import urllib.request
import urllib.error

USERNAME = "your-username"
PROJECT_DIR = f"/home/{USERNAME}/nh3_audit"
STREAMLIT_PORT = 8505
STREAMLIT_PROC = None

if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)


def start_streamlit():
    """在后台启动 Streamlit 进程"""
    global STREAMLIT_PROC
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{STREAMLIT_PORT}/", timeout=1)
        return  # 已在运行
    except Exception:
        pass

    STREAMLIT_PROC = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", f"{PROJECT_DIR}/app.py",
         "--server.port", str(STREAMLIT_PORT),
         "--server.headless", "true",
         "--server.enableCORS", "false",
         "--server.enableXsrfProtection", "false",
         "--server.enableWebsocketCompression", "false",
         "--browser.gatherUsageStats", "false",
         "--server.fileWatcherType", "none"],
        cwd=PROJECT_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(3)


def _proxy(environ, start_response):
    """HTTP 反向代理到 Streamlit"""
    path = environ.get("PATH_INFO", "/")
    query = environ.get("QUERY_STRING", "")
    url = f"http://127.0.0.1:{STREAMLIT_PORT}{path}"
    if query:
        url += "?" + query

    # WebSocket 在免费账号 WSGI 模式下不支持，给出友好提示
    if environ.get("HTTP_UPGRADE", "").lower() == "websocket":
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return ["""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Streamlit 需要 WebSocket</title></head><body style="font-family:sans-serif;padding:40px;">
<h2>连接需要 WebSocket 支持</h2>
<p>PythonAnywhere 免费账号的 WSGI 代理不支持 WebSocket。</p>
<p>请考虑以下方案：</p>
<ul>
<li>升级到 <b>PythonAnywhere 付费账号</b> ($5/月) 并启用 Always-on task</li>
<li>或使用 <b>Streamlit Cloud</b> 免费部署: <a href="https://streamlit.io/cloud">streamlit.io/cloud</a></li>
</ul>
</body></html>""".encode("utf-8")]

    try:
        method = environ["REQUEST_METHOD"]
        content_length = int(environ.get("CONTENT_LENGTH", 0) or 0)
        body = environ["wsgi.input"].read(content_length) if content_length else None

        req = urllib.request.Request(url, data=body, method=method)
        for hdr_key in ("CONTENT_TYPE", "HTTP_ACCEPT",
                        "HTTP_USER_AGENT", "HTTP_COOKIE"):
            val = environ.get(hdr_key)
            if val:
                name = hdr_key.replace("HTTP_", "").replace("_", "-").title()
                req.add_header(name, val)

        with urllib.request.urlopen(req, timeout=30) as resp:
            resp_body = resp.read()
            resp_headers = [(k, v) for k, v in resp.getheaders()
                          if k.lower() not in ("transfer-encoding", "connection")]

        start_response(f"{resp.getcode()} OK", resp_headers)
        return [resp_body]

    except urllib.error.HTTPError as e:
        start_response(f"{e.code} Error", [("Content-Type", "text/plain")])
        return [f"HTTP {e.code}".encode()]
    except Exception as e:
        start_response("502 Bad Gateway",
                      [("Content-Type", "text/html; charset=utf-8")])
        return [f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>启动中</title><meta http-equiv="refresh" content="3">
</head><body style="font-family:sans-serif;padding:40px;">
<h2>Streamlit 正在启动...</h2><p>请稍候，页面将自动刷新。</p>
<p>如果长时间未响应，请在 PythonAnywhere Console 中运行:</p>
<pre>cd {PROJECT_DIR} && python start_streamlit.py</pre>
</body></html>""".encode("utf-8")]


def application(environ, start_response):
    start_streamlit()
    return _proxy(environ, start_response)
