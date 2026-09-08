#!/usr/bin/env python3
from pathlib import Path

path = Path('native/src/app/Main.cpp')
text = path.read_text(encoding='utf-8')
old = 'std::clamp(std::stod(altitudeEnv), 800.0, 80000.0)'
new = 'std::clamp(std::stod(altitudeEnv), 800.0, 2000000.0)'
count = text.count(old)
if count == 0 and new in text:
    print('R24 orbital evidence altitude already enabled')
    raise SystemExit(0)
if count != 1:
    raise SystemExit(f'capture altitude clamp anchor expected once, found {count}')
text = text.replace(old, new, 1)
path.write_text(text, encoding='utf-8')
print('R24 orbital evidence altitude enabled: max=2000000m')
