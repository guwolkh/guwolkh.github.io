"""내 컴퓨터에서 미리보기: python serve.py → http://localhost:8080

페이지를 새로고침할 때마다 다시 빌드하므로, 파일을 고친 뒤 새로고침만 하면 됩니다.
빌드 중 오류가 나면 서버는 꺼지지 않고 화면에 오류 내용을 보여 줍니다.
"""
import functools
import http.server
import importlib
import socketserver
import threading
import traceback
from html import escape

import build

PORT = 8080
BUILD_LOCK = threading.Lock()  # 동시에 두 번 빌드하면 dist 폴더가 엉킵니다


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]
        if path.endswith("/") or path.endswith(".html"):
            with BUILD_LOCK:
                return self._build_then_serve()
        super().do_GET()

    def _build_then_serve(self):
        try:
            importlib.reload(build)  # build.py 를 고쳐도 바로 반영
            build.main()
        except BaseException as err:  # sys.exit 포함
            if isinstance(err, KeyboardInterrupt):
                raise
            msg = traceback.format_exc() if not isinstance(err, SystemExit) else str(err)
            body = f"<meta charset=utf-8><h1>빌드 오류</h1><pre>{escape(msg)}</pre>".encode("utf-8")
            self.send_response(500)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()


if __name__ == "__main__":
    build.main()
    handler = functools.partial(Handler, directory=str(build.DIST))
    # 여러 요청을 동시에 처리해야 브라우저 연결 하나 때문에 멈추지 않습니다
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    socketserver.ThreadingTCPServer.daemon_threads = True
    with socketserver.ThreadingTCPServer(("127.0.0.1", PORT), handler) as httpd:
        print(f"미리보기: http://localhost:{PORT}  (끄려면 Ctrl+C)")
        httpd.serve_forever()
