# -*- coding: utf-8 -*-
"""Reader/writer for .n16 files: KT-style wrapper but often UNCOMPRESSED (comp_size=0
means the body is raw, not LZ4). Body is the same 0x134C58 string-table section format
used by strdata.bin/ev_strdata.bin (see apply_translations.py's read_strtable_raw)."""
import struct
import lz4.block

def n16_unwrap(blob):
    """Return (header24, dec_bytes). Handles both flags 00-01(stored) and 01-01(LZ4)."""
    dec_size = struct.unpack_from('<Q', blob, 8)[0]
    comp_size = struct.unpack_from('<Q', blob, 16)[0]
    if comp_size == 0:
        body = blob[24:24+dec_size]
        assert len(body) == dec_size, (len(body), dec_size)
        return blob[:24], body, False   # False = was stored uncompressed
    else:
        body = lz4.block.decompress(blob[24:24+comp_size], uncompressed_size=dec_size)
        return blob[:24], body, True

def n16_wrap(header24, data, compressed):
    hdr = bytearray(header24)
    if compressed:
        comp = lz4.block.compress(data, mode='high_compression', compression=12, store_size=False)
        struct.pack_into('<Q', hdr, 8, len(data))
        struct.pack_into('<Q', hdr, 16, len(comp))
        return bytes(hdr) + comp
    else:
        struct.pack_into('<Q', hdr, 8, len(data))
        struct.pack_into('<Q', hdr, 16, 0)
        return bytes(hdr) + data

def read_strtable_sections(dec):
    """Same layout as apply_translations.read_strtable_raw but returns (offset,size) too
    for each section, useful for files with a SINGLE top-level count+toc like strdata."""
    count = struct.unpack_from('<I', dec, 0)[0]
    sections = []
    for i in range(count):
        off, size = struct.unpack_from('<II', dec, 4 + i*8)
        sections.append((off, size))
    return sections

def esc(cus):
    s = ''
    for cu in cus:
        if cu == 0x1B: s += '<ESC>'
        elif cu == 0x0A: s += '\\n'
        elif cu == 0x09: s += '\\t'
        elif cu == 0x5C: s += '\\\\'
        elif cu < 0x20: s += f'<{cu:02X}>'
        else: s += chr(cu)
    return s

def unesc(s):
    import re
    out = []
    i = 0
    while i < len(s):
        c = s[i]
        if c == '\\' and i + 1 < len(s):
            n = s[i + 1]
            if n == 'n': out.append(0x0A); i += 2; continue
            if n == 't': out.append(0x09); i += 2; continue
            if n == '\\': out.append(0x5C); i += 2; continue
        if c == '<':
            if s[i:i+5] == '<ESC>': out.append(0x1B); i += 5; continue
            m = re.match(r'<([0-9A-F]{2})>', s[i:i+4])
            if m: out.append(int(m.group(1), 16)); i += 4; continue
        out.append(ord(c)); i += 1
    return out

def read_section_strings(dec, off, size):
    """Read one 0x134C58 string-table section at dec[off:off+size]; return list of escaped strings."""
    magic = struct.unpack_from('<I', dec, off)[0]
    assert magic == 0x134C58, hex(magic)
    n = struct.unpack_from('<H', dec, off+8)[0]
    tab = off + 0x14
    offs = struct.unpack_from(f'<{n}I', dec, tab)
    out = []
    for e in offs:
        pos = tab + e
        cus = []
        while True:
            cu = struct.unpack_from('<H', dec, pos)[0]
            pos += 2
            if cu == 0: break
            cus.append(cu)
        out.append(esc(cus))
    return out

def build_section(strings):
    n = len(strings)
    table = bytearray()
    pool = bytearray()
    base = 4 * n
    for s in strings:
        table += struct.pack('<I', base + len(pool))
        cus = unesc(s)
        pool += struct.pack(f'<{len(cus)}H', *cus) if cus else b''
        pool += b'\x00\x00'
    body = bytes(table) + bytes(pool)
    size = 0x14 + len(body)
    hdr = struct.pack('<IIIII', 0x134C58, 0x10000 | (size & 0xFFFF),
                      0x40000 | n, 0x14, 0xFFFFFF00)
    return hdr + body
