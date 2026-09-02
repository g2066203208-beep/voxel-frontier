# NeoForge 1.21.1 Mod Dev

Private development workspace for Minecraft Java Edition 1.21.1 + NeoForge.

## Baseline

- Minecraft: 1.21.1
- NeoForge: 21.1.249
- Java: 21
- Build plugin: ModDevGradle 2.0.146
- CI Gradle: 9.2.1

The baseline follows the official NeoForge 1.21.1 ModDevGradle MDK and NeoForge getting-started guidance.

## Remote development loop

1. Edit mod source/resources in GitHub.
2. GitHub Actions compiles the mod with Java 21.
3. Inspect build failures and stack traces.
4. Fix code and rerun until the build passes.
5. Upload the built JAR as the `mod-jar` workflow artifact.

## Local game testing

For tests that require the actual Minecraft client, clone the repository onto a PC with JDK 21. A Gradle wrapper will be added/generated for the local workflow; until then, Gradle 9.2.1 can run the development tasks directly.

Useful tasks after the workspace is complete:

```text
gradle build
gradle runClient
gradle runServer
gradle runGameTestServer
```

## Placeholder mod

The current bootstrap mod id is `moddev`. It exists only to verify the NeoForge development pipeline and will be renamed when the real mod project is defined.
