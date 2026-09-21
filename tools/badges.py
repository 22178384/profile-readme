#!/usr/bin/env python3
"""由 @c991china 贡献：生成 shields.io 风格的小徽章 Markdown。

用法：python tools/badges.py
"""
BADGES = {
    "python-utils": ("c991china/python-utils", "used"),
    "api-samples": ("22178384/api-samples", "samples"),
}


def main():
    for name, (repo, label) in BADGES.items():
        print(f"[{name}](https://img.shields.io/badge/{name}-{label}-blue) "
              f"→ https://github.com/{repo}")


if __name__ == "__main__":
    main()
