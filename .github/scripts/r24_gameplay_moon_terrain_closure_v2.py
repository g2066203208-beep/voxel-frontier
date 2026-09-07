from pathlib import Path

source_path = Path('.github/scripts/r24_gameplay_moon_terrain_closure.py')
source = source_path.read_text(encoding='utf-8')

bad = r'''replace_once(
    header,
    """    double volcano{};\n    double river{};\n\n    // Subordinate geomorphology/climate fields.\n""",
    """    double volcano{};\n    double river{};\n    double alluvialFan{};\n\n    // Subordinate geomorphology/climate fields.\n""",
)'''

good = r'''replace_once(
    header,
    """    double volcano{};\n    double river{};\n""",
    """    double volcano{};\n    double river{};\n    double alluvialFan{};\n""",
)'''

if bad not in source:
    raise SystemExit('v2: expected legacy header anchor not found in closure script')
source = source.replace(bad, good, 1)

namespace = {'__name__': '__main__', '__file__': str(source_path)}
exec(compile(source, str(source_path), 'exec'), namespace)
