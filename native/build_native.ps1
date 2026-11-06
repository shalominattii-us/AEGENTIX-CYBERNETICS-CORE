# Build AEGENTIX native hot-path library (optional; Python falls back if absent)
$ErrorActionPreference='Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$src = Join-Path $here 'aegentix_fast.c'
$out = Join-Path $here 'aegentix_fast.dll'
if (Get-Command cl -ErrorAction SilentlyContinue) {
  cl /nologo /LD /O2 /W3 /DNDEBUG "$src" /link /OUT:"$out"
  exit $LASTEXITCODE
}
if (Get-Command clang -ErrorAction SilentlyContinue) {
  clang -O3 -shared -DNDEBUG -o "$out" "$src"
  exit $LASTEXITCODE
}
if (Get-Command gcc -ErrorAction SilentlyContinue) {
  gcc -O3 -shared -DNDEBUG -o "$out" "$src"
  exit $LASTEXITCODE
}
Write-Warning 'No C compiler found (cl/clang/gcc). Native fast-path remains optional; Python fallback active.'
exit 2
