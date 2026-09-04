#include "PlanetShaders.hpp"

#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>
#include <string_view>

namespace {

constexpr std::uint32_t kSpirvMagicNumber = 0x07230203U;
constexpr std::uint16_t kSpirvOpEntryPoint = 15U;
constexpr std::uint32_t kSpirvExecutionModelVertex = 0U;
constexpr std::uint32_t kSpirvExecutionModelFragment = 4U;

[[noreturn]] void fail(std::string_view message) {
    std::cerr << "SHADER CONTRACT TEST FAILURE: " << message << '\n';
    std::exit(1);
}

void require(bool condition, std::string_view message) {
    if (!condition) fail(message);
}

[[nodiscard]] std::uint32_t loadWord(
    const unsigned char* bytes,
    std::size_t byteCount,
    std::size_t wordIndex) {
    const std::size_t byteOffset = wordIndex * 4U;
    require(byteOffset + 4U <= byteCount, "SPIR-V word read exceeds module size");
    return static_cast<std::uint32_t>(bytes[byteOffset])
        | (static_cast<std::uint32_t>(bytes[byteOffset + 1U]) << 8U)
        | (static_cast<std::uint32_t>(bytes[byteOffset + 2U]) << 16U)
        | (static_cast<std::uint32_t>(bytes[byteOffset + 3U]) << 24U);
}

[[nodiscard]] std::string readLiteralString(
    const unsigned char* bytes,
    std::size_t beginByte,
    std::size_t endByte) {
    require(beginByte < endByte, "SPIR-V entry-point string has no storage");
    std::string value;
    for (std::size_t i = beginByte; i < endByte; ++i) {
        const unsigned char byte = bytes[i];
        if (byte == 0U) return value;
        value.push_back(static_cast<char>(byte));
    }
    fail("SPIR-V entry-point string is not NUL terminated");
}

void validateEntryPoint(
    const unsigned char* bytes,
    std::size_t byteCount,
    std::uint32_t expectedExecutionModel,
    std::string_view expectedName) {
    require(bytes != nullptr, "SPIR-V byte pointer is null");
    require(byteCount >= 5U * sizeof(std::uint32_t), "SPIR-V module is smaller than its header");
    require((byteCount % sizeof(std::uint32_t)) == 0U, "SPIR-V module size is not word aligned");
    require(loadWord(bytes, byteCount, 0U) == kSpirvMagicNumber, "SPIR-V magic number is invalid");

    const std::size_t moduleWordCount = byteCount / sizeof(std::uint32_t);
    std::size_t instructionWord = 5U;
    std::uint32_t entryPointCount = 0U;
    bool foundExpected = false;

    while (instructionWord < moduleWordCount) {
        const std::uint32_t instruction = loadWord(bytes, byteCount, instructionWord);
        const std::uint16_t wordCount = static_cast<std::uint16_t>(instruction >> 16U);
        const std::uint16_t opcode = static_cast<std::uint16_t>(instruction & 0xFFFFU);
        require(wordCount > 0U, "SPIR-V instruction has zero word count");
        require(instructionWord + wordCount <= moduleWordCount, "SPIR-V instruction exceeds module bounds");

        if (opcode == kSpirvOpEntryPoint) {
            require(wordCount >= 4U, "OpEntryPoint instruction is truncated");
            ++entryPointCount;
            const std::uint32_t executionModel = loadWord(bytes, byteCount, instructionWord + 1U);
            const std::size_t nameBegin = (instructionWord + 3U) * 4U;
            const std::size_t instructionEnd = (instructionWord + wordCount) * 4U;
            const std::string name = readLiteralString(bytes, nameBegin, instructionEnd);
            if (executionModel == expectedExecutionModel && name == expectedName) foundExpected = true;
        }

        instructionWord += wordCount;
    }

    require(entryPointCount == 1U, "each embedded stage module must contain exactly one OpEntryPoint");
    require(foundExpected, "embedded SPIR-V OpEntryPoint does not match Vulkan pipeline pName/stage contract");
}

} // namespace

int main() {
    validateEntryPoint(
        vf::shaders::kPlanetVertexSpv,
        vf::shaders::kPlanetVertexSpvSize,
        kSpirvExecutionModelVertex,
        "vertexMain");
    validateEntryPoint(
        vf::shaders::kPlanetFragmentSpv,
        vf::shaders::kPlanetFragmentSpvSize,
        kSpirvExecutionModelFragment,
        "fragmentMain");
    validateEntryPoint(
        vf::shaders::kShadowVertexSpv,
        vf::shaders::kShadowVertexSpvSize,
        kSpirvExecutionModelVertex,
        "shadowVertexMain");
    validateEntryPoint(
        vf::shaders::kShadowFragmentSpv,
        vf::shaders::kShadowFragmentSpvSize,
        kSpirvExecutionModelFragment,
        "shadowFragmentMain");

    std::cout << "Shader SPIR-V entry-point contract tests passed\n";
    return 0;
}
