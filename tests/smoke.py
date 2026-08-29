import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from collector.core import validate_target, platform_family, commands_for_os
assert validate_target('192.0.2.10') == '192.0.2.10'
assert validate_target('example.com') == 'example.com'
try: validate_target('x;rm -rf /')
except ValueError: pass
else: raise AssertionError('unsafe target accepted')
assert commands_for_os()
print('smoke ok:', platform_family())
