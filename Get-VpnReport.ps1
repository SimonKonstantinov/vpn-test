param(
 [string]$Server = '77.221.138.191',
 [string]$Key = "$env:USERPROFILE\.ssh\codex_vps_key",
 [string]$OutputDirectory = "$env:USERPROFILE\Downloads",
 [string]$RemoteProject = '/home/ansible/vpn-test'
)
$ErrorActionPreference = 'Stop'
if ($RemoteProject -notmatch '^/[a-zA-Z0-9_/-]+$') { throw 'RemoteProject must be an absolute path without spaces or shell characters' }
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
& ssh -i $Key -o BatchMode=yes "ansible@$Server" "sudo ansible-playbook -i localhost, -c local $RemoteProject/report.yml"
if ($LASTEXITCODE -ne 0) { throw 'Report generation failed; files were not downloaded' }
foreach ($extension in @('html','json')) {
 $content = & ssh -i $Key -o BatchMode=yes "ansible@$Server" "sudo cat /var/log/vpn-report/latest.$extension"
 if ($LASTEXITCODE -ne 0) { throw "Cannot download $extension report" }
 $path = Join-Path $OutputDirectory "vpn-report.$extension"
 $content | Set-Content -LiteralPath $path -Encoding utf8
 Write-Output "Saved: $path"
}
Start-Process (Join-Path $OutputDirectory 'vpn-report.html')
