from __future__ import annotations


def parse_frontmatter(text: str) -> tuple[dict[str, str], str | None]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, "missing"
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            fields: dict[str, str] = {}
            frontmatter_lines = lines[1:index]
            line_index = 0
            while line_index < len(frontmatter_lines):
                raw_line = frontmatter_lines[line_index]
                if ":" not in raw_line or raw_line.lstrip().startswith("#"):
                    line_index += 1
                    continue
                key, value = raw_line.split(":", 1)
                key = key.strip()
                value = value.strip()
                if value in {">", "|", ">-", ">+", "|-", "|+"}:
                    block_lines: list[str] = []
                    line_index += 1
                    while line_index < len(frontmatter_lines):
                        block_line = frontmatter_lines[line_index]
                        if block_line.startswith((" ", "\t")) or not block_line.strip():
                            block_lines.append(block_line.strip())
                            line_index += 1
                            continue
                        break
                    if value.startswith(">"):
                        fields[key] = " ".join(part for part in block_lines if part).strip()
                    else:
                        fields[key] = "\n".join(block_lines).strip()
                    continue
                fields[key] = value.strip("\"'")
                line_index += 1
            return fields, None
    return {}, "unterminated"


def strip_frontmatter_fields(text: str, fields: set[str]) -> str:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return text
    for index in range(1, len(lines)):
        if lines[index].strip() != "---":
            continue
        filtered = [lines[0]]
        for line in lines[1:index]:
            key = line.split(":", 1)[0].strip() if ":" in line else ""
            if key not in fields:
                filtered.append(line)
        filtered.extend(lines[index:])
        return "".join(filtered)
    return text
