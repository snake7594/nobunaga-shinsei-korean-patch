import json, os

SP = os.path.dirname(os.path.abspath(__file__))
names = json.load(open(os.path.join(SP, 'hard_batches.json'), encoding='utf-8'))
sp_js = SP.replace('\\', '\\\\')

prompt_lines = [
    "'당신은 코에이 역사 게임 [노부나가의 야망 신생]의 일-한 번역가입니다. 아래는 이전에 검증(토큰/가나)에서 탈락한 어려운 항목들입니다.\\n' +",
    "'먼저 규칙 파일을 Read: ' + SP + '\\\\glossary.md\\n' +",
    "'배치 파일을 Read: ' + SP + '\\\\batches\\\\' + f + '\\n' +",
    "'각 항목 t를 한국어로 번역해 저장: ' + SP + '\\\\translated\\\\' + f + '\\n' +",
    "'출력 형식: {\"items\":[{\"i\":번호,\"t\":\"한국어\"}...]} (i·항목수 동일)\\n' +",
    "'=== 절대 규칙(위반 시 탈락) ===\\n' +",
    "'1) 줄바꿈 토큰(역슬래시+n)의 개수를 원문과 정확히 동일하게 유지. 위치도 각 줄 구조에 맞게 그대로. 임의로 줄을 합치거나 나누지 말 것.\\n' +",
    "'2) <ESC> 다음 두 글자(예 <ESC>CA <ESC>CZ <ESC>CB <ESC>CC)는 절대 변형·삭제·번역 금지. 감싼 본문만 번역.\\n' +",
    "'3) 대괄호 참조 토큰([b754] [bm826] [bs1871] 등)은 그대로 복사(내용은 게임이 이름으로 치환).\\n' +",
    "'4) 가운뎃점 ・, 전각괄호（）, 전각숫자, ※, 그리고 ㍉㎝㍑㌘㌣ 같은 전각 단위/기호 문자는 그대로 유지(버튼 아이콘이므로 번역 금지).\\n' +",
    "'5) %s %d 등 서식 지정자 유지.\\n' +",
    "'6) 번역문에 일본어 가나(히라가나·가타카나)가 하나도 남으면 안 됨. 한자도 모두 한글로. 인명·지명은 국립국어원 음차.\\n' +",
    "'7) 게임 용어는 glossary 표기 통일. 문어체/설명체.\\n' +",
    "'꼼꼼히 줄 단위로 대조하며 번역하세요. 완료 후 StructuredOutput으로 {file:\"' + f + '\", count:항목수} 반환.'",
]

script = f"""export const meta = {{
  name: 'shinsei-ko-hard',
  description: 'Retranslate hard-case (token-sensitive) strings with strict rules',
  phases: [{{ title: 'Translate', detail: 'strict token-preserving pass' }}],
}}

const SP = '{sp_js}'
const files = {json.dumps(names, separators=(',', ':'))}
const RESULT_SCHEMA = {{
  type: 'object',
  properties: {{ file: {{ type: 'string' }}, count: {{ type: 'integer' }} }},
  required: ['file', 'count'],
}}

const results = await pipeline(
  files,
  (f) => agent(
{chr(10).join('      ' + l for l in prompt_lines)},
    {{ label: 'hard:' + f, phase: 'Translate', schema: RESULT_SCHEMA, effort: 'high' }}
  )
)

const done = results.filter(Boolean)
log('done: ' + done.length + '/' + files.length)
return {{ completed: done.length, total: files.length, failed: files.filter((f, i) => !results[i]) }}
"""

out = os.path.join(SP, 'tr_hard.js')
with open(out, 'w', encoding='utf-8', newline='\n') as fp:
    fp.write(script)
print('written', out, len(script), 'chars')
