param([Parameter(Mandatory=$true)][string[]]$Links)
$ErrorActionPreference = 'Stop'
$results = @()
foreach ($url in $links) {
 $process = $null
 $configPath = Join-Path $PSScriptRoot 'temporary-test-client.json'
 try {
  $response = Invoke-WebRequest -Uri $url -TimeoutSec 20
  $decoded = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($response.Content.Trim()))
  $uri = [Uri]($decoded.Trim())
  $query = @{}
  foreach ($part in $uri.Query.TrimStart('?').Split('&')) { $pair = $part.Split('=',2); $query[[Uri]::UnescapeDataString($pair[0])] = [Uri]::UnescapeDataString($pair[1]) }
  $stream = @{network=$query['type'];security='reality';realitySettings=@{serverName=$query['sni'];fingerprint=$query['fp'];publicKey=$query['pbk'];shortId=$query['sid']}}
  if ($query['type'] -eq 'xhttp') { $stream.xhttpSettings = @{path=$query['path'];mode='auto'} }
  $user = @{id=$uri.UserInfo;encryption='none'}
  if ($query['flow']) { $user.flow=$query['flow'] }
  $config = @{log=@{loglevel='warning'};inbounds=@(@{listen='127.0.0.1';port=19081;protocol='socks';settings=@{auth='noauth';udp=$false}});outbounds=@(@{protocol='vless';settings=@{vnext=@(@{address=$uri.Host;port=$uri.Port;users=@($user)})};streamSettings=$stream})}
  if ($uri.Scheme -eq 'hysteria2') {
   $query['type'] = 'hysteria2'
   $config.outbounds = @(@{protocol='hysteria';settings=@{version=2;address=$uri.Host;port=$uri.Port};streamSettings=@{network='hysteria';security='tls';tlsSettings=@{serverName=$uri.Host;alpn=@('h3');allowInsecure=$false};hysteriaSettings=@{version=2;auth=[Uri]::UnescapeDataString($uri.UserInfo)}}})
  }
  $config | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $configPath -Encoding utf8
  $process = Start-Process -FilePath 'C:\Program Files\FlyFrogLLC\Happ\core\xray.exe' -ArgumentList @('run','-config',('"'+$configPath+'"')) -WindowStyle Hidden -PassThru -RedirectStandardError (Join-Path $PSScriptRoot 'test-client-errors.log') -RedirectStandardOutput (Join-Path $PSScriptRoot 'test-client.log')
  Start-Sleep -Seconds 2
  if ($process.HasExited) { throw 'Test Xray failed to start; inspect local error log' }
  $result = & curl.exe --fail --silent --show-error --max-time 25 --proxy socks5h://127.0.0.1:19081 -w '|%{time_total}' https://api.ipify.org
  $results += [pscustomobject]@{name=[Uri]::UnescapeDataString($uri.Fragment.TrimStart('#'));transport=$query['type'];port=$uri.Port;curl_exit=$LASTEXITCODE;ip_and_seconds=$result;tested_at=(Get-Date -Format o)}
 } catch { $results += [pscustomobject]@{error=$_.Exception.Message;tested_at=(Get-Date -Format o)} }
 finally {
  if ($process -and -not $process.HasExited) { Stop-Process -Id $process.Id }
  if (Test-Path -LiteralPath $configPath) { Remove-Item -LiteralPath $configPath }
 }
}
$results | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $PSScriptRoot 'pc-subscription-test.json') -Encoding utf8
$results | Format-List
