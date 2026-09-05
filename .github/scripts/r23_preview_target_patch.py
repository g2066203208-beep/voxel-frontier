from pathlib import Path

path = Path("native/src/app/Main.cpp")
text = path.read_text(encoding="utf-8")
anchor = '        const std::uint32_t moonId = celestial.addBody(luna);\n'
insert = '''        const std::uint32_t moonId = celestial.addBody(luna);\n        if (const char* celestialTargetEnv = std::getenv("VF_CELESTIAL_TARGET");\n            celestialTargetEnv != nullptr && *celestialTargetEnv != '\\0') {\n            const std::string_view celestialTarget{celestialTargetEnv};\n            if (celestialTarget == "sun") {\n                camera.setViewDirectionWorld(\n                    sun.position - camera.position(), camera.up());\n                std::cout << "R23 celestial target: sun\\n";\n            } else if (celestialTarget == "moon") {\n                camera.setViewDirectionWorld(\n                    luna.position - camera.position(), camera.up());\n                std::cout << "R23 celestial target: moon\\n";\n            }\n        }\n'''
if anchor not in text:
    raise SystemExit("R23 celestial target patch anchor missing")
text = text.replace(anchor, insert, 1)
path.write_text(text, encoding="utf-8")
print("R23 celestial target patch applied")
