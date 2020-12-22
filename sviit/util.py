SWE_CHARS = {
    "}": "å",
    "{": "ä",
    "|": "ö",
    "]": "Å",
    "[": "Ä",
    "\\": "Ö",
}

SWE_CHARS_INVERSE = {v:k for k, v in SWE_CHARS.items()}

def str_to_swechar(s: str) -> str:
    return "".join(token_to_swechar(ord(c)) for c in s)

def str_from_swechar(s: str) -> str:
    return "".join(token_from_swechar(ord(c)) for c in s)


def bytes_to_swechar(bstr: bytes) -> str:
    return "".join(token_to_swechar(byte) for byte in bstr)

def bytes_from_swechar(bstr: bytes) -> str:
    return "".join(token_from_swechar(byte) for byte in bstr)


def token_to_swechar(token: int) -> str:
    return SWE_CHARS.get(chr(token), chr(token))

def token_from_swechar(token: int) -> str:
    return SWE_CHARS_INVERSE.get(chr(token), chr(token))
