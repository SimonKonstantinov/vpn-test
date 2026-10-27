param([string]$Server = '77.221.138.191', [string]$Key = "$env:USERPROFILE\.ssh\codex_vps_key")
Write-Host 'Keep this window open. Grafana: http://127.0.0.1:3000 ; Panel: http://127.0.0.1:2053/panel/'
& ssh -i $Key -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -N -L 3000:127.0.0.1:3000 -L 2053:127.0.0.1:2053 "ansible@$Server"
exit $LASTEXITCODE
