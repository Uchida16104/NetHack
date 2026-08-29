function netHackApp(){
  return {
    agent:{ok:false,status:'Checking…'}, browserPlatform:navigator.userAgentData?.platform || navigator.platform || 'Unknown',
    target:'', port:443, report:null, sqlDb:null,
    async init(){
      try{ const r=await fetch('http://127.0.0.1:8765/health',{cache:'no-store'}); if(r.ok){this.agent={ok:true,status:'Online'}} else throw new Error(); }
      catch(e){ this.agent={ok:false,status:'Offline — local agent required'} }
      if(window.Motion?.animate){ Motion.animate('[data-motion="hero"]',{opacity:[0,1],y:[12,0]},{duration:.45,easing:'ease-out'}); }
      await this.initSQL();
    },
    async initSQL(){
      try{ const SQL=await initSqlJs({locateFile:f=>`https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.13.0/${f}`}); this.sqlDb=new SQL.Database(); this.sqlDb.run('CREATE TABLE IF NOT EXISTS reports (id INTEGER PRIMARY KEY AUTOINCREMENT, collected_at TEXT, platform TEXT, hostname TEXT, target TEXT, raw_json TEXT NOT NULL);'); }catch(e){ console.error(e); }
    },
    async collectOnly(){
      await this.fetchAgent(`http://127.0.0.1:8765/collect`);
    },
    async runAgentReport(){
      const t=this.target.trim(); if(!t){ alert('hostnameまたはIPを入力してください。'); return; }
      const u=new URL('http://127.0.0.1:8765/report'); u.searchParams.set('target',t); if(this.port) u.searchParams.set('port',String(this.port));
      await this.fetchAgent(u.toString());
    },
    async fetchAgent(url){
      try{ const r=await fetch(url,{cache:'no-store'}); const data=await r.json(); if(!r.ok) throw new Error(data.error||'agent error'); this.report=data; this.agent={ok:true,status:'Online'}; await this.persist(); }
      catch(e){ this.agent={ok:false,status:'Unavailable'}; alert(`ローカル診断エージェントに接続できません。\n\n${e.message}\n\n先に python collector/agent.py を起動してください。`); }
    },
    async persist(){
      if(!this.sqlDb||!this.report) return;
      const esc=v=>String(v??'').replace(/'/g,"''");
      const sql=`INSERT INTO reports(collected_at,platform,hostname,target,raw_json) VALUES ('${esc(this.report.collected_at)}','${esc(this.report.platform)}','${esc(this.report.hostname)}','${esc(this.report.target?.target||'')}','${esc(JSON.stringify(this.report))}');`;
      try{ this.sqlDb.run(sql); }catch(e){ console.error(e); }
    },
    summaryCards(){
      const cmds=this.report?.commands||[]; const ok=cmds.filter(x=>x.returncode===0).length; const failed=cmds.length-ok;
      return [{k:'Platform',v:this.report?.platform||'—'},{k:'Commands OK',v:ok},{k:'Commands non-zero',v:failed},{k:'Resolved IPs',v:this.report?.target?.resolved_ips?.length||0}];
    },
    pretty(v){ return v?JSON.stringify(v,null,2):'—'; },
    download(name,mime,text){ const a=document.createElement('a'); a.href=URL.createObjectURL(new Blob([text],{type:mime})); a.download=name; a.click(); setTimeout(()=>URL.revokeObjectURL(a.href),1000); },
    exportJSON(){ if(this.report) this.download('nethack-report.json','application/json;charset=utf-8',JSON.stringify(this.report,null,2)); },
    csvCell(v){ let s=String(v??''); return `"${s.replaceAll('"','""')}"`; },
    exportCSV(){ if(!this.report)return; const rows=[['section','name','returncode','duration_ms','stdout','stderr'],...(this.report.commands||[]).map(c=>['command',c.name,c.returncode,c.duration_ms,c.stdout,c.stderr])]; if(this.report.target) rows.push(['target','probe','', '',JSON.stringify(this.report.target), '']); const text='\uFEFF'+rows.map(r=>r.map(this.csvCell).join(',')).join('\r\n'); this.download('nethack-report.csv','text/csv;charset=utf-8',text); },
    sqlValue(v){return `'${String(v??'').replaceAll("'","''")}'`;},
    exportSQL(){ if(!this.report)return; const s=`-- NetHack UTF-8 SQL export\nCREATE TABLE IF NOT EXISTS reports (id INTEGER PRIMARY KEY AUTOINCREMENT, collected_at TEXT, platform TEXT, hostname TEXT, target TEXT, raw_json TEXT NOT NULL);\nINSERT INTO reports(collected_at,platform,hostname,target,raw_json) VALUES (${this.sqlValue(this.report.collected_at)},${this.sqlValue(this.report.platform)},${this.sqlValue(this.report.hostname)},${this.sqlValue(this.report.target?.target||'')},${this.sqlValue(JSON.stringify(this.report))});\n`; this.download('nethack-report.sql','application/sql;charset=utf-8','\uFEFF'+s); },
    async copyReport(){ if(this.report) await navigator.clipboard.writeText(JSON.stringify(this.report,null,2)); }
  }
}
