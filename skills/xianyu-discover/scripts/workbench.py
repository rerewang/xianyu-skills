#!/usr/bin/env python3
"""Read or mutate the local selection workflow using the workbench's validations."""
import argparse,json,sys
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--root',type=Path,required=True,help='Folder containing app.py and data/research.sqlite3')
p.add_argument('action',choices=['status','data','project','keyword','create','review','update','check'])
p.add_argument('--file',type=Path,help='UTF-8 JSON payload for write operations')
a=p.parse_args();root=a.root.resolve()
if not (root/'app.py').is_file() or not (root/'data/research.sqlite3').is_file():p.error('工作台路径无效；不能静默新建数据库')
sys.path.insert(0,str(root));import app
if a.action in ('status','data','check'):
 d=app.dataset();flow=d['workflow']
 if a.action=='data':result=d
 else:
  result={'projects':[{k:v for k,v in r.items() if k!='batches'} for r in flow['projects']],
   'opportunities':[{k:o[k] for k in ('id','project_id','name','status','reason','next_action','missing')} for o in flow['opportunities']]}
  if a.action=='check':
   result['unassigned_observations']=flow['unassigned_observations']
   result['unreviewed']=sum(p['total']-p['reviewed'] for p in flow['projects'])
   result['uncertain']=sum(r['disposition']=='待核验' for r in flow['reviews'])
   result['warning']='初筛覆盖只统计已关联关键词的方向；旧版未纳入流程的样本仍需认领，不能报告全库已评估。'
else:
 if not a.file:p.error('写入操作需要 --file JSON文件')
 body=json.loads(a.file.read_text())
 result=app.opportunity(body) if a.action=='update' else app.workflow_action(dict(body,action=a.action))
print(json.dumps(result,ensure_ascii=False,indent=2))
