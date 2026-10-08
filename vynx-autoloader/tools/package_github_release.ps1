param(
  [string]$OutputPath,
  [string]$ReleaseDirectory,
  [switch]$Force
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem

$repo = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$baseVersion = [regex]::Match(
  [System.IO.File]::ReadAllText((Join-Path $repo 'include/vynx.h')),
  '#define\s+VYNX_VERSION\s+"([^"]+)"'
).Groups[1].Value
$versionedRelease = Join-Path $repo "release-v$baseVersion"
$release = if ($ReleaseDirectory) {
  [System.IO.Path]::GetFullPath($ReleaseDirectory)
} elseif (Test-Path -LiteralPath $versionedRelease -PathType Container) {
  [System.IO.Path]::GetFullPath($versionedRelease)
} else {
  [System.IO.Path]::GetFullPath((Join-Path $repo 'release'))
}
$hostFiles = @(Get-ChildItem -LiteralPath $release -File -Filter 'vynx-autoloader-host_v*.py')
if ($hostFiles.Count -ne 1) {
  throw "Expected one versioned host script in '$release'; found $($hostFiles.Count). Run build_release.sh first."
}

$match = [regex]::Match($hostFiles[0].Name, '^vynx-autoloader-host_v(.+)\.py$')
if (-not $match.Success) { throw "Could not read release version from '$($hostFiles[0].Name)'." }
$version = $match.Groups[1].Value
$required = @(
  $hostFiles[0].FullName,
  (Join-Path $release "vynx-autoloader-installer_v$version.elf"),
  (Join-Path $release '.START-HOST.bat'),
  (Join-Path $release 'README.md'),
  (Join-Path $release 'THIRD_PARTY_NOTICES.md'),
  (Join-Path $release 'LICENSE')
)
foreach ($path in $required) {
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
    throw "Release file is missing: $path. Run build_release.sh first."
  }
}

if (-not $OutputPath) {
  $OutputPath = Join-Path (Split-Path -Parent $repo) "Vynx.dev-Autoloader-v$version-GitHub-Release.zip"
}
$OutputPath = [System.IO.Path]::GetFullPath($OutputPath)
$outputDirectory = Split-Path -Parent $OutputPath
if (-not (Test-Path -LiteralPath $outputDirectory -PathType Container)) {
  New-Item -ItemType Directory -Path $outputDirectory | Out-Null
}
if (Test-Path -LiteralPath $OutputPath) {
  if (-not $Force) { throw "Output already exists: $OutputPath. Use -Force to replace this generated archive." }
  Remove-Item -LiteralPath $OutputPath -Force
}

$files = @(
  Get-ChildItem -LiteralPath $release -File -Recurse |
    Where-Object { $_.FullName -notmatch '[\\/](__pycache__|\.git)([\\/]|$)' }
)
if (-not ($files | Where-Object Name -EQ 'icon0.png')) {
  throw "The release folder has no icon0.png. Run build_release.sh first."
}
if (-not (Test-Path -LiteralPath (Join-Path $release 'licenses') -PathType Container)) {
  throw "The release folder has no licenses directory. Run build_release.sh first."
}

$archive = [System.IO.Compression.ZipFile]::Open(
  $OutputPath,
  [System.IO.Compression.ZipArchiveMode]::Create
)
try {
  foreach ($file in $files) {
    $entryName = [System.IO.Path]::GetRelativePath($release, $file.FullName).Replace('\', '/')
    [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
      $archive, $file.FullName, $entryName,
      [System.IO.Compression.CompressionLevel]::Optimal
    ) | Out-Null
  }
} finally {
  $archive.Dispose()
}

Write-Output "Created $OutputPath"
Get-Item -LiteralPath $OutputPath | Select-Object FullName,Length,LastWriteTime
Get-FileHash -Algorithm SHA256 -LiteralPath $OutputPath | Select-Object Path,Hash
