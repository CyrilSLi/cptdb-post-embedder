# Built-in modules
import re
from base64 import urlsafe_b64encode, urlsafe_b64decode

# 3rd-party modules
from diff_match_patch import diff_match_patch

_b63alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-"

def b63encode(num):
    if num == 0:
        return _b63alphabet[0]
    result = []
    while num > 0:
        num, rem = divmod(num, 63)
        result.append(_b63alphabet[rem])
    return "".join(reversed(result))

def b64encode(text):
    return urlsafe_b64encode(text.encode()).decode().rstrip("=")

def b63decode(text):
    value = 0
    for char in text:
        if char not in _b63alphabet:
            raise ValueError(f"Invalid urlsafe base63 character: {char}")
        value = value * 63 + _b63alphabet.index(char)
    return value

def b64decode(text):
    return urlsafe_b64decode(text + "=" * (-len(text) % 4)).decode()

class minimal_dmp(diff_match_patch):
    # Format: <pos>[_len][.data]~<pos>[_len][.data]~...
    # Replace: pos_len.data, Delete: pos_len, Insert: pos.data
    # data is a base64-enconded string, pos and len are base63-encoded integers [0-9A-Za-z\-]
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
                    out.append(f"{b63encode(pos)}_{b63encode(length)}.{b64encode(repl_data)}")
                    pos += len(repl_data)
                    i += 1 # skip the next insert op since it's part of this replace
                else: # Delete
                    out.append(f"{b63encode(pos)}_{b63encode(length)}")
            elif op == 1: # Insert
                out.append(f"{b63encode(pos)}.{b64encode(data)}")
                pos += length

            i += 1
        return "~".join(out)

    def patch(self, text, patch):
        ops = []
        for item in patch.split("~"):
            if not item.strip():
                continue
            pos, length, data = re.fullmatch(r"([0-9A-Za-z\-]+)(_[0-9A-Za-z\-]+)?(.[0-9A-Za-z\-_]+)?", item.strip()).groups()
            ops.append((
                b63decode(pos),
                b63decode(length[1:]) if length else None,
                b64decode(data[1:]) if data else None
            ))

        for pos, length, data in ops:
            if length is not None and data is not None: # Replace
                text = text[:pos] + data + text[pos + length:]
            elif length is not None: # Delete
                text = text[:pos] + text[pos + length:]
            elif data is not None: # Insert
                text = text[:pos] + data + text[pos:]
            else:
                raise ValueError("length and data cannot both be omitted")
        return text

if __name__ == "__main__":
    while True:
        dmp = minimal_dmp()
        print("Minimal DMP Demo")
        a = input("Original txt (A): ")
        b = input("Modified txt (B): ")
        patch = dmp.diff(a, b)
        print("Diff (A ----> B):", patch)
        result = dmp.patch(a, patch)
        print("Patch (A + Diff):", repr(result)[1:-1])
        print("Patch successful:", result == b)
        reverse_patch = dmp.diff(b, a)
        print("Diff (B ----> A):", reverse_patch)
        reverse_result = dmp.patch(b, reverse_patch)
        print("Patch (B + Diff):", repr(reverse_result)[1:-1])
        print("Patch successful:", reverse_result == a)
        if input("Try again? (y/N): ").lower() != "y":
            break