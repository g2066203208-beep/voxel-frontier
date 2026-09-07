from pathlib import Path

v2 = Path('.github/scripts/r24_gameplay_moon_terrain_closure_v2.py')
namespace = {'__name__': '__main__', '__file__': str(v2)}
exec(compile(v2.read_text(encoding='utf-8'), str(v2), 'exec'), namespace)

main = Path('native/src/app/Main.cpp')
text = main.read_text(encoding='utf-8')
old = '        constexpr std::uint32_t evidenceSamples = 16384U;\n'
new = ('        // Evidence-only global target scan: 8192 Fibonacci directions retain full-sphere '
       'coverage while keeping deterministic Vulkan capture startup bounded.\n'
       '        constexpr std::uint32_t evidenceSamples = 8192U;\n')
if text.count(old) != 1:
    raise SystemExit(f'v3: expected one evidenceSamples anchor, found {text.count(old)}')
main.write_text(text.replace(old, new, 1), encoding='utf-8')
print('R24 gameplay Moon + causal terrain closure V3 applied')
