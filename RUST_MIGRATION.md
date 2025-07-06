## 🤝 Agent Collaboration Plan: Migrate TypeScript NPM Package to Rust Crate

### 📅 Objective

Replicate the functionality of an existing TypeScript NPM package in Rust, ensuring API parity, type fidelity, and equivalent test coverage. Optionally expose the Rust crate back to JavaScript consumers via WASM or FFI. This includes a full migration of the testing and CI checks that are currently configured to run via pre-commit hook and within GitHub Actions, such that the depth and breadth of all checks is preserved, if not improved. It includes all dependencies. The migration must preserve 100% of the functionality down to the most minor detail and ergonomics such that the end user has no idea it took place other than the fact that it's going to be much, much faster.

---

### 🧠 System Decomposition

1. **Source Analysis**: Analyze TS package structure, dependencies, and logic.
2. **Rust Target Design**: Architect a Rust crate mirroring the TS design.
3. **Functionality Translation**: Port implementation in idiomatic Rust.
4. **Bindings (Optional)**: Generate WASM or FFI layer for JS interop.
5. **Validation & Testing**: Recreate tests in Rust to ensure behavioral parity.

---

### 🤖 Swarm Agent Collaboration Model

| Role                 | Objective                                       | Dependencies                 | Outputs                         |
| -------------------- | ----------------------------------------------- | ---------------------------- | ------------------------------- |
| `source-analyst`     | Extract TS APIs, logic flow, and module graph   | None                         | Interface schema, logic graph   |
| `api-translator`     | Define Rust APIs to match TS structure          | `source-analyst`             | Rust API surface specification  |
| `type-modeler`       | Convert TS types to idiomatic Rust              | `api-translator`             | Enums, structs, traits          |
| `core-dev`           | Implement modules in Rust                       | `type-modeler`               | Core Rust source code           |
| `bindings-architect` | Expose Rust crate to JS via WASM/FFI (optional) | `core-dev`                   | JS-compatible Rust interface    |
| `test-engineer`      | Recreate test suite and CI harness              | `core-dev`, `source-analyst` | Rust test coverage + CI setup   |
| `perf-auditor`       | Benchmark Rust vs TS versions                   | `core-dev`                   | Performance optimization report |
| `doc-writer`         | Generate Rustdoc + README from TS documentation | `core-dev`, `source-analyst` | Crate documentation             |

---

### 🧬 Sequencing and Execution

1. **Source Analysis** ➔ `source-analyst`
2. **API + Type Translation** ➔ `api-translator`, `type-modeler`
3. **Rust Core Implementation** ➔ `core-dev`
4. **Optional WASM/FFI Binding** ➔ `bindings-architect`
5. **Test Porting + Validation** ➔ `test-engineer`
6. **Benchmarking & Optimization** ➔ `perf-auditor`
7. **Documentation Finalization** ➔ `doc-writer`
8. **Crate/NPM Release**

---

Would you like this template adapted to a specific TypeScript package?
