# BennuGD2 (macOS Apple Silicon)

This fork is focused on building and running BennuGD2 on macOS Apple Silicon (M1/M2/M3).

## Requirements

Install dependencies with Homebrew:

```bash
brew install cmake sdl2 sdl2_image sdl2_mixer glew libogg libvorbis theora pkg-config
```

## Build Engine (macOS arm64)

```bash
git submodule update --init --recursive

cd vendor
./build-sdl-gpu.sh macos-arm64 clean

cd ..
./build.sh macos-arm64 clean use_sdl2_gpu
```

This generates `bgdc`, `bgdi`, and runtime modules in:

`build/macos-arm64/bin`

## Prebuilt Apple Silicon Binaries in Repository

This repository also includes prebuilt macOS arm64 binaries in:

- `binaries/macos-arm64/bin`
- `binaries/macos-arm64/Frameworks/SDL2_gpu.framework`

## Compile a Game

From the repository root:

```bash
./compile games/Goody/Goody.prg
```

This generates:

`games/Goody/Goody.dcb`

## Execute a Game

Compile and run in one step:

```bash
./run games/Goody/Goody.prg
```

Run an existing `DCB`:

```bash
./run games/Goody/Goody.dcb
```

## Manual CLI (without helper scripts)

If you prefer raw CLI commands:

```bash
cd games/Goody
../../build/macos-arm64/bin/bgdc Goody.prg
../../build/macos-arm64/bin/bgdi Goody.dcb
```

Or from repository root:

```bash
build/macos-arm64/bin/bgdc games/Goody/Goody.prg
cd games/Goody
../../build/macos-arm64/bin/bgdi Goody.dcb
```

## Typical Workflow

```bash
./compile games/Goody/Goody.prg
./run games/Goody/Goody.dcb
```

## Package for Distribution (.app + .dmg)

```bash
./package-macos games/Goody/Goody.prg
```

Outputs:

- `dist/macos-arm64/Goody.app`
- `dist/macos-arm64/Goody-macos-arm64.dmg`

Use `--no-dmg` if you only want the `.app` bundle:

```bash
./package-macos games/Goody/Goody.prg --no-dmg
```

## License

This project is licensed under the MIT License. See [LICENSE.md](LICENSE.md).
