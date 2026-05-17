from pathlib import Path
import os
import webbrowser


PROJECT_ROOT = Path(__file__).resolve().parent
HTML_PATH = PROJECT_ROOT / "templates" / "profile.html"


def open_local_html(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"找不到 HTML 文件: {path}")

    if os.name == "nt":
        os.startfile(str(path))
        return

    opened = webbrowser.open(path.as_uri())
    if not opened:
        raise RuntimeError(f"无法自动打开浏览器: {path}")


def main() -> None:
    open_local_html(HTML_PATH)
    print(f"已打开本地页面: {HTML_PATH}")


if __name__ == "__main__":
    main()
