#!/usr/bin/env python3
"""根据 sections/ 下的片段拼装 README.md（演示可程序化生成个人主页）。

用法：python tools/build_readme.py
"""
import os

SECTIONS = ["intro.md", "projects.md", "links.md"]


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    parts = []
    for sec in SECTIONS:
        p = os.path.join(here, sec)
        if os.path.exists(p):
            parts.append(open(p, encoding="utf-8").read().strip())
    readme = "\n\n".join(parts) + "\n"
    with open(os.path.join(here, "..", "..", "README.md"), "w", encoding="utf-8") as fh:
        fh.write(readme)
    print("README.md 已重新生成。")


if __name__ == "__main__":
    main()
