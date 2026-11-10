import json,re,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'reports/proven-baseline-four-task-retry-output'
RESULTS=OUT/'results/mini_benchmark'
manifest={x['instance_id']:x for x in (json.loads(line) for line in (ROOT/'starter/official/tasks.jsonl').read_text(encoding='utf-8').splitlines() if line.strip())}
diag=json.loads((OUT/'mini_benchmark_diagnostic.json').read_text(encoding='utf-8'))
rows=[json.loads(x) for x in (RESULTS/'task_results.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
print('DIAGNOSTIC',json.dumps({k:diag.get(k) for k in ['total_tasks','resolved_tasks','resolution_rate','context_compaction_events']},indent=2))
all_ok=True
for row in rows:
 tid=row['instance_id']; patch=RESULTS/'patches'/f'{tid}.patch'; test=RESULTS/'test_outputs'/f'{tid}.log'; trace=RESULTS/'traces'/f'trace_{tid}.json'
 resolved=bool(row.get('resolved')) and row.get('test_exit_code')==0
 patch_exists=patch.is_file() and patch.stat().st_size>0
 test_text=test.read_text(encoding='utf-8',errors='replace') if test.is_file() else ''
 pass_match=re.search(r'(\d+) passed',test_text)
 test_passes=bool(pass_match and int(pass_match.group(1))>0)
 trace_data=json.loads(trace.read_text(encoding='utf-8')) if trace.is_file() else {}
 tool_calls=sum(len(s.get('tool_calls',[]) or []) for s in trace_data.get('steps',[]))
 llm_calls=sum(s.get('llm_call_count',0) or 0 for s in trace_data.get('steps',[]))
 commands=[]
 for s in trace_data.get('steps',[]):
  for tc in s.get('tool_calls',[]) or []:
   args=tc.get('arguments') or tc.get('args') or {}
   if isinstance(args,str):
    try: args=json.loads(args)
    except: pass
   if isinstance(args,dict) and isinstance(args.get('command'),str): commands.append(args['command'])
 dup=sum(n-1 for n in collections.Counter(commands).values() if n>1)
 ref=manifest.get(tid,{}).get('patch','')
 added=lambda x:{z for z in x.splitlines() if z.startswith('+') and not z.startswith('+++')}
 patch_match=bool(ref and patch_exists and added(patch.read_text(encoding='utf-8'))==added(ref))
 print(f'{tid}: resolved={row.get("resolved")} exit={row.get("test_exit_code")} duration={row.get("duration_seconds")}s tools={row.get("tool_calls")} trace_tools={tool_calls} llm={llm_calls} patch={patch_exists} testlog_pass={test_passes} added_lines_match_reference={patch_match} duplicate_commands={dup}')
 if not resolved: all_ok=False
print('TASKS',len(rows),'ALL_RESOLVED_AND_TESTED',all_ok)
print('SUMMARY',json.dumps(json.loads((RESULTS/'summary.json').read_text(encoding='utf-8')),indent=2))
