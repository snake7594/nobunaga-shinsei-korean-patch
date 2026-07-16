import sys, importlib.util
sys.stdout.reconfigure(encoding='utf-8')
spec = importlib.util.spec_from_file_location('ap', r'C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad\apply_translations.py')
ap = importlib.util.module_from_spec(spec)
sys.modules['ap'] = ap
spec.loader.exec_module.__self__ if False else None
# load module without running main
import types
src = open(r'C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad\apply_translations.py', encoding='utf-8').read()
src = src.replace("if __name__ == '__main__':\n    main()", '')
mod = types.ModuleType('ap2')
mod.__file__ = r'C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad\apply_translations.py'
exec(src, mod.__dict__)
tr, stats, fails, src_items, missing = mod.load_translations()

terms = ['知行','代官','評定','出陣','外交','親善','交渉','朝廷','報告','調略','領内諸策','政策','取引',
         'セーブ','ロード','環境設定','ヘルプ','機能','元服','髪結い','登用','移動','転封','城下施設',
         '郡開発','本拠','具申','主命','軍議','部隊編制','合戦結果','論功行賞','シナリオ選択','勢力選択',
         '武将情報','国衆情報','家宝選択','解雇','縁組','賞罰','隠居','配属','削除','編集','情報','鑑賞',
         '武将名鑑','引継','税率','攻略目標','新設','編制','解散','登録武将編集','姫情報','役職']
for t in terms:
    print(f'{t} = {tr.get(t, "(없음)")}')
