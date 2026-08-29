(function () {
  'use strict';

  function createNetHackApp() {
    return {
      agent: { ok: false, status: 'Checking…' },
      browserPlatform: navigator.userAgentData?.platform || navigator.platform || 'Unknown',
      target: '',
      port: 443,
      report: null,
      sqlDb: null,

      async init() {
        await this.checkAgent();

        if (window.Motion?.animate) {
          try {
            window.Motion.animate(
              '[data-motion="hero"]',
              { opacity: [0, 1], y: [12, 0] },
              { duration: 0.45, easing: 'ease-out' }
            );
          } catch (error) {
            console.warn('Motion animation skipped:', error);
          }
        }

        await this.initSQL();
      },

      async checkAgent() {
        try {
          const response = await fetch('http://127.0.0.1:8765/health', {
            cache: 'no-store',
            mode: 'cors'
          });
          if (!response.ok) throw new Error(`HTTP ${response.status}`);
          this.agent = { ok: true, status: 'Online' };
        } catch (error) {
          console.info('Local agent unavailable:', error?.message || error);
          this.agent = { ok: false, status: 'Offline — local agent required' };
        }
      },

      async initSQL() {
        try {
          if (typeof window.initSqlJs !== 'function') {
            console.warn('sql.js is not loaded. SQL export remains available without browser DB.');
            return;
          }

          const SQL = await window.initSqlJs({
            locateFile: (file) =>
              `https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.13.0/${file}`
          });

          this.sqlDb = new SQL.Database();
          this.sqlDb.run(
            `CREATE TABLE IF NOT EXISTS reports (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              collected_at TEXT,
              platform TEXT,
              hostname TEXT,
              target TEXT,
              raw_json TEXT NOT NULL
            );`
          );
        } catch (error) {
          console.error('sql.js initialization failed:', error);
          this.sqlDb = null;
        }
      },

      async collectOnly() {
        await this.fetchAgent('http://127.0.0.1:8765/collect');
      },

      async runAgentReport() {
        const target = String(this.target || '').trim();
        if (!target) {
          window.alert('hostnameまたはIPを入力してください。');
          return;
        }

        const url = new URL('http://127.0.0.1:8765/report');
        url.searchParams.set('target', target);

        const parsedPort = Number(this.port);
        if (Number.isInteger(parsedPort) && parsedPort >= 1 && parsedPort <= 65535) {
          url.searchParams.set('port', String(parsedPort));
        }

        await this.fetchAgent(url.toString());
      },

      async fetchAgent(url) {
        try {
          const response = await fetch(url, {
            cache: 'no-store',
            mode: 'cors'
          });

          let data = null;
          try {
            data = await response.json();
          } catch {
            throw new Error(`Agent returned non-JSON response (HTTP ${response.status})`);
          }

          if (!response.ok) {
            throw new Error(data?.error || `Agent HTTP ${response.status}`);
          }

          this.report = data;
          this.agent = { ok: true, status: 'Online' };
          this.persist();
        } catch (error) {
          this.agent = { ok: false, status: 'Unavailable' };
          console.error('Agent request failed:', error);
          window.alert(
            `ローカル診断エージェントに接続できません。\n\n${
              error?.message || error
            }\n\n先に python collector/agent.py を起動してください。`
          );
        }
      },

      persist() {
        if (!this.sqlDb || !this.report) return;

        const esc = (value) => String(value ?? '').replaceAll("'", "''");
        const target = this.report.target?.target || '';
        const sql = `INSERT INTO reports(
          collected_at, platform, hostname, target, raw_json
        ) VALUES (
          '${esc(this.report.collected_at)}',
          '${esc(this.report.platform)}',
          '${esc(this.report.hostname)}',
          '${esc(target)}',
          '${esc(JSON.stringify(this.report))}'
        );`;

        try {
          this.sqlDb.run(sql);
        } catch (error) {
          console.error('sql.js persistence failed:', error);
        }
      },

      summaryCards() {
        const commands = this.report?.commands || [];
        const ok = commands.filter((command) => command.returncode === 0).length;
        const failed = commands.length - ok;

        return [
          { k: 'Platform', v: this.report?.platform || '—' },
          { k: 'Commands OK', v: ok },
          { k: 'Commands non-zero', v: failed },
          { k: 'Resolved IPs', v: this.report?.target?.resolved_ips?.length || 0 }
        ];
      },

      pretty(value) {
        return value ? JSON.stringify(value, null, 2) : '—';
      },

      download(name, mime, text) {
        const blob = new Blob([text], { type: mime });
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement('a');
        anchor.href = url;
        anchor.download = name;
        document.body.appendChild(anchor);
        anchor.click();
        anchor.remove();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
      },

      exportJSON() {
        if (!this.report) return;
        this.download(
          'nethack-report.json',
          'application/json;charset=utf-8',
          JSON.stringify(this.report, null, 2)
        );
      },

      csvCell(value) {
        const text = String(value ?? '');
        return `"${text.replaceAll('"', '""')}"`;
      },

      exportCSV() {
        if (!this.report) return;

        const rows = [
          ['section', 'name', 'returncode', 'duration_ms', 'stdout', 'stderr']
        ];

        for (const command of this.report.commands || []) {
          rows.push([
            'command',
            command.name,
            command.returncode,
            command.duration_ms,
            command.stdout,
            command.stderr
          ]);
        }

        if (this.report.target) {
          rows.push([
            'target',
            'probe',
            '',
            '',
            JSON.stringify(this.report.target),
            ''
          ]);
        }

        const text =
          '\uFEFF' +
          rows.map((row) => row.map((value) => this.csvCell(value)).join(',')).join('\r\n');

        this.download('nethack-report.csv', 'text/csv;charset=utf-8', text);
      },

      sqlValue(value) {
        return `'${String(value ?? '').replaceAll("'", "''")}'`;
      },

      exportSQL() {
        if (!this.report) return;

        const sql = `-- NetHack UTF-8 SQL export\n` +
          `CREATE TABLE IF NOT EXISTS reports (` +
          `id INTEGER PRIMARY KEY AUTOINCREMENT, ` +
          `collected_at TEXT, platform TEXT, hostname TEXT, target TEXT, raw_json TEXT NOT NULL` +
          `);\n` +
          `INSERT INTO reports(collected_at,platform,hostname,target,raw_json) VALUES (` +
          `${this.sqlValue(this.report.collected_at)},` +
          `${this.sqlValue(this.report.platform)},` +
          `${this.sqlValue(this.report.hostname)},` +
          `${this.sqlValue(this.report.target?.target || '')},` +
          `${this.sqlValue(JSON.stringify(this.report))}` +
          `);\n`;

        this.download(
          'nethack-report.sql',
          'application/sql;charset=utf-8',
          '\uFEFF' + sql
        );
      },

      async copyReport() {
        if (!this.report) return;

        try {
          await navigator.clipboard.writeText(JSON.stringify(this.report, null, 2));
        } catch (error) {
          console.error('Clipboard write failed:', error);
          window.alert('クリップボードへのコピーに失敗しました。');
        }
      }
    };
  }

  // Register the component before Alpine starts. This avoids ReferenceError
  // from expressions such as @click="runAgentReport()" in CSP/CDN environments.
  document.addEventListener('alpine:init', () => {
    window.Alpine.data('netHackApp', createNetHackApp);
  });

  // Also expose the factory globally as a defensive fallback for pages where
  // Alpine evaluates x-data before the alpine:init listener is attached.
  window.netHackApp = createNetHackApp;
})();
