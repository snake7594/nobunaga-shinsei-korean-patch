"""Export game strings: strdata/ev_strdata (offset-table sections) and msggame (bytecode) to TSV."""
import struct, sys, io
sys.stdout.reconfigure(encoding='utf-8')

def esc_vis(cus):
    s = ''
    for cu in cus:
        if cu == 0x1B: s += '<ESC>'
        elif cu == 0x0A: s += '\\n'
        elif cu == 0x09: s += '\\t'
        elif cu < 0x20: s += f'<{cu:02X}>'
        else: s += chr(cu)
    return s

def export_strtable(path, out_path):
    with open(path, 'rb') as f:
        d = f.read()
    count = struct.unpack_from('<I', d, 0)[0]
    lines = []
    for i in range(count):
        off, size = struct.unpack_from('<II', d, 4 + i*8)
        f2 = struct.unpack_from('<I', d, off + 8)[0]
        n = f2 & 0xFFFF
        tab = off + 0x14
        entries = struct.unpack_from(f'<{n}I', d, tab)
        for j, e in enumerate(entries):
            pos = tab + e
            cus = []
            while pos + 1 < len(d):
                cu = struct.unpack_from('<H', d, pos)[0]
                pos += 2
                if cu == 0:
                    break
                cus.append(cu)
            lines.append(f'{i}\t{j}\t{esc_vis(cus)}')
    with io.open(out_path, 'w', encoding='utf-8') as f:
        f.write('section\tindex\ttext\n')
        f.write('\n'.join(lines))
    print(f'{out_path}: {len(lines)} strings')

def export_msggame(path, out_path):
    with open(path, 'rb') as f:
        d = f.read()
    count = struct.unpack_from('<I', d, 0)[0]
    lines = []
    n_text = 0
    for i in range(count):
        off, size = struct.unpack_from('<II', d, 4 + i*8)
        n = struct.unpack_from('<I', d, off)[0]
        offs = struct.unpack_from(f'<{n}I', d, off + 4)
        ends = list(offs[1:]) + [size]
        for j in range(n):
            blob = d[off+offs[j]:off+ends[j]]
            # extract text runs between 07 07 01 and 07 07 02
            texts = []
            p = 0
            while True:
                st = blob.find(b'\x07\x07\x01', p)
                if st < 0:
                    break
                en = blob.find(b'\x07\x07\x02', st + 3)
                if en < 0:
                    break
                raw = blob[st+3:en]
                cus = struct.unpack_from(f'<{len(raw)//2}H', raw)
                texts.append(esc_vis(cus))
                p = en + 3
            if texts:
                n_text += 1
                lines.append(f'{i}\t{j}\t' + '<SEP>'.join(texts))
    with io.open(out_path, 'w', encoding='utf-8') as f:
        f.write('section\tentry\ttext_runs\n')
        f.write('\n'.join(lines))
    print(f'{out_path}: {n_text} entries with text')

base = sys.argv[1]
export_strtable(base + r'\msg_jp_strdata.dec', base + r'\jp_strdata.tsv')
export_strtable(base + r'\msg_jp_ev_strdata.dec', base + r'\jp_ev_strdata.tsv')
export_msggame(base + r'\msg_jp_msggame.dec', base + r'\jp_msggame.tsv')

# compare msggame JP vs SC entry counts
for tag in ('jp', 'sc'):
    with open(base + rf'\msg_{tag}_msggame.dec', 'rb') as f:
        d = f.read()
    count = struct.unpack_from('<I', d, 0)[0]
    ns = []
    for i in range(count):
        off, size = struct.unpack_from('<II', d, 4 + i*8)
        ns.append(struct.unpack_from('<I', d, off)[0])
    print(f'msggame {tag}: sections={count} entry counts={ns}')
