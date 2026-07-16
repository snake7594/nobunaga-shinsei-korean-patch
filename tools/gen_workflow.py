import json, os, sys

SP = os.path.dirname(os.path.abspath(__file__))
list_file = sys.argv[1] if len(sys.argv) > 1 else 'batch_names.json'
out_file = sys.argv[2] if len(sys.argv) > 2 else 'tr_workflow.js'
names = json.load(open(os.path.join(SP, list_file), encoding='utf-8'))
sp_js = SP.replace('\\', '\\\\')

prompt_lines = [
    "'당신은 코에이 역사 전략게임 [노부나가의 야망 신생]의 일-한 번역가입니다.\\n' +",
    "'1) 규칙 파일을 Read 도구로 읽으세요: ' + SP + '\\\\glossary.md\\n' +",
    "'2) 배치 파일을 읽으세요: ' + SP + '\\\\batches\\\\' + f + '\\n' +",
    "'3) 모든 항목의 t를 한국어로 번역해 다음 경로에 UTF-8 JSON으로 저장하세요:\\n' +",
    "'   ' + SP + '\\\\translated\\\\' + f + '\\n' +",
    "'   출력 형식: {\"items\":[{\"i\":번호,\"t\":\"한국어\"}...]} - i 값과 항목 수는 입력과 동일해야 합니다.\\n' +",
    "'핵심 규칙: <ESC>xx 태그, <16진수> 토큰, 줄바꿈 토큰(백슬래시n), %s 등 서식은 그대로 보존(개수 동일).\\n' +",
    "'인명·지명은 국립국어원 일본어 표기법으로 음차. 번역문에 가나·한자가 남으면 안 됩니다(한글/숫자/기호만).\\n' +",
    "'cat=' + cat + ' 문체 규칙을 적용하세요.\\n' +",
    "'완료 후 StructuredOutput으로 {file:\"' + f + '\", count:저장한 항목 수}를 반환하세요.'",
]

script = f"""export const meta = {{
  name: 'shinsei-ko-tr-resume',
  description: 'Translate Nobunaga Shinsei strings JA-KO (remaining batches)',
  phases: [{{ title: 'Translate', detail: 'one agent per batch file' }}],
}}

const SP = '{sp_js}'
const files = {json.dumps(names, separators=(',', ':'))}
const RESULT_SCHEMA = {{
  type: 'object',
  properties: {{ file: {{ type: 'string' }}, count: {{ type: 'integer' }} }},
  required: ['file', 'count'],
}}
const EFFORT = {{ name: 'low', ui: 'low', desc: 'medium', dialog: 'medium' }}

const results = await pipeline(
  files,
  (f) => {{
    const cat = f.split('_')[1].split('.')[0]
    return agent(
      {chr(10).join('      ' + l for l in prompt_lines)},
      {{ label: 'tr:' + f, phase: 'Translate', schema: RESULT_SCHEMA, effort: EFFORT[cat] || 'medium' }}
    )
  }}
)

const done = results.filter(Boolean)
log('translated batches: ' + done.length + '/' + files.length)
return {{
  completed: done.length,
  total: files.length,
  failed: files.filter((f, i) => !results[i]),
}}
"""

out = os.path.join(SP, out_file)
with open(out, 'w', encoding='utf-8', newline='\n') as fp:
    fp.write(script)
print('written', out, len(script), 'chars')
