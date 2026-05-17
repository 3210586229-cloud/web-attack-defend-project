from pathlib import Path
from threading import Timer
from typing import Optional
import webbrowser

from flask import Flask, abort, render_template, send_file,requests


app = Flask(__name__)
HOST = "127.0.0.1"
PORT = 5000


def first_existing_path(*candidates: str) -> Optional[Path]:
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return path
    return None


MEDIA_FILES = {
    "avatar": first_existing_path(
        r"C:\Users\byd\Pictures\化学有机\下载.webp",
        r"C:\Users\byd\Pictures\Camera Roll\zidan.png",
        r"C:\Users\byd\Pictures\Camera Roll\dayun.jpg",
    ),
    "video1": first_existing_path(
        r"C:\Users\byd\Videos\NVIDIA\League of Legends\League of Legends 2026.02.28 - 21.09.54.01.mp4",
    ),
    "video2": first_existing_path(
        r"C:\Users\byd\Videos\NVIDIA\Yuan Shen 原神\Yuan Shen 原神 2026.02.21 - 16.42.35.02.mp4",
    ),
}


@app.route("/")
@app.route("/桌面")
@app.route("/C:/Users/byd/Documents/桌面")
def profile():
    return render_template("profile.html")


@app.route("/media/<name>")
def media(name: str):
    path = MEDIA_FILES.get(name)
    if path is None or not path.exists():
        abort(404)
    return send_file(path, conditional=True)


if __name__ == "__main__":
    Timer(1, lambda: webbrowser.open(f"http://{HOST}:{PORT}/")).start()
    app.run(host=HOST, port=PORT, debug=False, use_reloader=False)




