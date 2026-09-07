from pathlib import Path

path = Path('native/src/app/Main.cpp')
text = path.read_text(encoding='utf-8')

block = '''        const bool captureHighSpeed = [] {
            const char* value = std::getenv("VF_CAPTURE_HIGH_SPEED");
            return value != nullptr && std::string_view{value} == "1";
        }();
        const bool runtimeDiagnosticsStdout = [] {
            const char* value = std::getenv("VF_RUNTIME_DIAGNOSTICS");
            return value != nullptr && std::string_view{value} == "1";
        }();
        if (captureHighSpeed) {
            camera.setFlightMode(true);
            camera.setCreativeFlightSpeedMps(500000.0);
            std::cout << "R24 capture high-speed initial_speed_mps=500000\\n";
        }
'''

count = text.count(block)
if count < 1:
    raise SystemExit('capture configuration block not found')
if count > 1:
    first = text.find(block)
    head = text[:first + len(block)]
    tail = text[first + len(block):]
    tail = tail.replace(block, '')
    text = head + tail

if text.count('const bool captureHighSpeed = []') != 1:
    raise SystemExit('captureHighSpeed declaration is not unique after cleanup')
if text.count('const bool runtimeDiagnosticsStdout = []') != 1:
    raise SystemExit('runtimeDiagnosticsStdout declaration is not unique after cleanup')

path.write_text(text, encoding='utf-8')
print(f'collapsed {count} capture configuration blocks to one')
