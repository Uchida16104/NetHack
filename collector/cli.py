import argparse, json
from pathlib import Path
try:
    from .core import full_report
except ImportError:
    from core import full_report

p = argparse.ArgumentParser(description='NetHack authorized network diagnostics')
p.add_argument('--target')
p.add_argument('--port', type=int)
p.add_argument('--json', dest='json_path', type=Path)
args = p.parse_args()
report = full_report(args.target, args.port)
text = json.dumps(report, ensure_ascii=False, indent=2)
if args.json_path:
    args.json_path.write_text(text, encoding='utf-8')
else:
    print(text)
