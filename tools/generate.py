"""根据配置生成一个简单的 profile README（示例）。"""

import json
import os


def generate(repos: list[str]) -> str:
    lines = ["# 22178384\n", "> 喜欢把零散工具整理成仓库的人。\n", "## 我维护的生态\n"]
    for r in repos:
        lines.append(f"- {r}\n")
    return "".join(lines)


if __name__ == "__main__":
    repos = ["api-samples", "project-seed", "tutorial-zh", "snippet-box",
             "algo-practice", "ci-templates", "data-tools", "web-demos", "yaml-configs"]
    out = os.path.join(os.path.dirname(__file__), "..", "README.generated.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(generate(repos))
    print("已生成 README.generated.md")
