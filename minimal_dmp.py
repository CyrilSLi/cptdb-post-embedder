# Built-in modules
import re
from base64 import urlsafe_b64encode, urlsafe_b64decode

# 3rd-party modules
from diff_match_patch import diff_match_patch

def minimal_b64encode(text):
    return urlsafe_b64encode(text.encode()).decode().rstrip("=")
def minimal_b64decode(text):
    padding = "=" * (-len(text) % 4)
    return urlsafe_b64decode(text + padding).decode()

class minimal_dmp(diff_match_patch):
    # Format: <pos><op>[len][~data]_<pos><op>[len][~data]_...
    # Ops: . Insert, - Delete, ~ Replace
    def diff(self, a, b):
        diffs = self.diff_main(a, b)
        pos, i = 0, 0
        out = []
        while i < len(diffs):
            op, data = diffs[i]
            length = len(data)

            if op == 0: # Equal
                pos += length
            elif op == -1:
                if i + 1 < len(diffs) and diffs[i + 1][0] == 1: # Replace
                    repl_data = diffs[i + 1][1]
                    out.append(f"{pos}~{length}~{minimal_b64encode(repl_data)}")
                    pos += len(repl_data)
                    i += 1 # skip the next insert op since it's part of this replace
                else: # Delete
                    out.append(f"{pos}-{length}")
            elif op == 1: # Insertion
                out.append(f"{pos}.~{minimal_b64encode(data)}")
                pos += length
            
            i += 1
        return "_".join(out)

    def patch(self, text, patch):
        ops = []
        for item in patch.split("_"):
            if not item.strip():
                continue
            pos, op, length, data = re.fullmatch(r"(\d+)([.\-~])(\d+)?(~[a-zA-Z0-9\-_]+)?", item.strip()).groups()
            ops.append((
                int(pos),
                op,
                int(length) if length else None,
                minimal_b64decode(data[1:]) if data else None
            ))

        for pos, op, length, data in ops:
            match op:
                case ".":
                    text = text[:pos] + data + text[pos:]
                case "-":
                    text = text[:pos] + text[pos + length:]
                case "~":
                    text = text[:pos] + data + text[pos + length:]
        return text