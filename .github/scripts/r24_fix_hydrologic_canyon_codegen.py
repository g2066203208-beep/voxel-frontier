from pathlib import Path

MAIN = Path('native/src/app/Main.cpp')
text = MAIN.read_text(encoding='utf-8')
broken = '<< " relief_m=" << hydrologicRelief << \'\n\';'
fixed = '<< " relief_m=" << hydrologicRelief << \'\\n\';'

if broken in text:
    text = text.replace(broken, fixed, 1)
elif fixed not in text:
    raise SystemExit('hydrologic canyon newline literal anchor not found')

MAIN.write_text(text, encoding='utf-8')
print('R24 hydrologic canyon generated newline literal repaired')
