# Contributing to SketchyUp

Thanks for your interest. Development happens mainly on Arch Linux (Omarchy). This page covers building, testing and opening a pull request. For how the project is planned, see the [build plan](docs/BUILD_PLAN.md) and the [roadmap](docs/PR_ROADMAP.md). For a map of all documentation, see [docs/README.md](docs/README.md).

## Build and run

You need CMake 3.25+, Ninja, a C++20 compiler, Qt 6.8+ (base and Wayland development packages), OpenSSL 3 development headers and OpenGL 3.3. Python 3 is required for the default verification targets (`BUILD_TESTING=ON`). On Arch:

```sh
sudo pacman -S --needed cmake ninja gcc pkgconf python qt6-base qt6-wayland wayland openssl
```

Build, test and run the desktop app:

```sh
cmake --preset dev
cmake --build --preset dev --parallel 2
ctest --preset dev
./build/dev/sketchyup --demo
```

The pinned geometry dependencies are vendored in `third_party/`; CMake never downloads code. See [measured evidence and limitations](docs/verification/native-spike.md).

For the core alone, with no Qt or graphical session:

```sh
cmake --preset headless
cmake --build --preset headless
ctest --preset headless
```

`CMakePresets.json` also defines `sanitize` and the IFC and `.skp` helper presets (`ifc`, `ifc-app`, `skp` and their sanitizer variants) that CI uses.

**Keep memory in check.** A full build and the large-model tests can use several GiB. Build with `--parallel 2` on machines with less than 32 GiB of RAM, and run `ctest` with at most `-j2`.

## Viewport verification

The [viewport follow-up](docs/verification/R002-viewport.md) records native pixel, picking, GPU-cache and context-recreation checks, including both physical display scales. Run `build/dev/viewport_tests` in a graphical session. Its `--benchmark` option measures independent triangle buffers; add `--instanced` for the repeated-triangle comparison.

## Arch package

```sh
./scripts/package-source.sh /tmp/sketchyup-package
cd /tmp/sketchyup-package
makepkg -s
```

The script creates a source archive and writes its checksum into the generated PKGBUILD. The package contains the native app, the CLI, the desktop entry, the icon, the MIME definition and the license notices. [Clean Arch acceptance](docs/verification/R014-package.md) covers install, desktop launch, upgrade, reopen and removal. The [package workflow](packaging/arch/README.md) explains how to reproduce it, including the optional `sketchyup-ifc` package.

## Screenshots

The README images in [`docs/images`](docs/images/) are generated, not hand-made. See [docs/images/README.md](docs/images/README.md) to regenerate them after an interface change.

## Pull requests

- **One change per pull request**, linked to its roadmap entry where there is one. Fill in the [PR opening and review contract](docs/PR_ROADMAP.md#pr-opening-and-review-contract).
- **CI decides the merge.** Each pull request runs a fast tier chosen by what it changes ([ADR 0170](docs/decisions/0170-ci-tiers.md)), and it merges when the single `CI verdict` check is green. Label a risky change `full-ci` to run every platform and scale, then push or re-run; adding the label alone does not start a run.
- **Record evidence.** A change in behavior updates its decision record in [`docs/decisions`](docs/decisions/) and, where it has acceptance evidence, a summary in [`docs/verification`](docs/verification/). Never commit credentials, private models or large raw recordings.
- **Test with synthetic data.** Build fixtures with the scripting commands or a generator. Never commit a model someone else made.
- **Naming.** No product, feature, menu, package or file name may contain "SketchUp". Describing `.skp` format versions ("SketchUp 2024 files") is fine.
- **Style.** Format C++ with the repository's `.clang-format`. Write documentation in plain, direct English.

## Reporting problems

Open an [issue](https://github.com/zygote55/sketchyup/issues/new/choose). For a security problem, follow [SECURITY.md](SECURITY.md) instead of opening a public issue.
