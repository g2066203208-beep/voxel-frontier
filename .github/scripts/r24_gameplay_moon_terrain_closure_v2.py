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

# VF_TERRAIN_TARGET is an evidence-only deterministic province selector. Sampling the complete
# procedural stack 16k times delayed the first Vulkan frame on CI and could time out before a
# screenshot even though the terrain itself compiled and passed all tests. 4096 Fibonacci samples
# still resolve the narrow process maxima used by the evidence targets while bounding startup cost.
main_path = Path('native/src/app/Main.cpp')
main = main_path.read_text(encoding='utf-8')
old = 'constexpr std::uint32_t evidenceSamples = 16384U;'
new = 'constexpr std::uint32_t evidenceSamples = 4096U;'
if main.count(old) != 1:
    raise SystemExit(f'v2: expected exactly one terrain evidence sample-count anchor, found {main.count(old)}')
main_path.write_text(main.replace(old, new, 1), encoding='utf-8')
print('R24 evidence scan bounded to 4096 deterministic samples')
