# Next-engine merge criteria

Before replacing the compatibility engine as the default path, the next engine must demonstrate:

- green native C++ correctness tests;
- green WebAssembly SIMD release build;
- green strict TypeScript/WebGPU integration build;
- stable browser startup on supported WebGPU hardware;
- chunk streaming without full-world rebuilds;
- gameplay feature parity for destruction/building, collision, inventory and survival;
- measured frame-time improvements on representative desktop hardware.
