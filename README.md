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

## Compile a Game

Use the helper script:

```bash
./compile games/Goody/Goody.prg
```

Output:

`games/Goody/Goody.dcb`

## Run a Game

```bash
./run games/Goody/Goody.prg
```

Or run an existing DCB directly:

```bash
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
