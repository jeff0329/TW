param(
    [string]$OutputDir = "data/raw_tourism_v2"
)

$ErrorActionPreference = 'Stop'

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$files = @{
    'Attraction-json.zip' = 'https://media.taiwan.net.tw/XMLReleaseAll_public/v2.0/Zh_tw/Attraction-json.zip'
    'Restaurant-json.zip' = 'https://media.taiwan.net.tw/XMLReleaseAll_public/v2.0/Zh_tw/Restaurant-json.zip'
    'Hotel-json.zip' = 'https://media.taiwan.net.tw/XMLReleaseAll_public/v2.0/Zh_tw/Hotel-json.zip'
    'Event-json.zip' = 'https://media.taiwan.net.tw/XMLReleaseAll_public/v2.0/Zh_tw/Event-json.zip'
}

foreach ($name in $files.Keys) {
    $zipPath = Join-Path $OutputDir $name
    $extractDir = Join-Path $OutputDir ($name -replace '\.zip$','')

    Write-Host "Downloading $name ..."
    Invoke-WebRequest -Uri $files[$name] -OutFile $zipPath

    if (Test-Path $extractDir) {
        Remove-Item -Path $extractDir -Recurse -Force
    }

    Expand-Archive -Path $zipPath -DestinationPath $extractDir -Force
    Write-Host "Extracted to $extractDir"
}

Write-Host "Done. Files are in $OutputDir"
