import struct, sys, glob, json, os
import lz4.block
sys.stdout.reconfigure(encoding='utf-8')
SP = os.path.dirname(os.path.abspath(__file__))

# translated unique count
tr = 0
for tf in glob.glob(os.path.join(SP, 'translated', '*.json')):
    try:
        d = json.load(open(tf, encoding='utf-8'))
        tr += len([1 for it in d.get('items', []) if it.get('t', '').strip()])
    except Exception:
        pass
manifest = json.load(open(os.path.join(SP, 'batch_manifest.json'), encoding='utf-8'))
total_batches = len(manifest)
done_batches = len(glob.glob(os.path.join(SP, 'translated', '*.json')))
total_strings = sum(m['count'] for m in manifest)
print(f'batches: {done_batches}/{total_batches}')
print(f'unique source strings: {total_strings:,}')
print(f'translated (raw): {tr:,}')

# report validation
os.system(f'python "{SP}\\apply_translations.py" "{SP}\\dummy" --report-only')
