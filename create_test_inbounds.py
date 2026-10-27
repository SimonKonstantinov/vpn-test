import copy
import json
import secrets
import subprocess
import urllib.request
import uuid

base = 'http://127.0.0.1:2053/panel/panel/api/inbounds/'
token = subprocess.check_output(['docker', 'exec', 'vpn-3x-ui', '/app/x-ui', 'setting', '-getApiToken'], text=True).split('apiToken:')[1].strip()

def api(path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(base + path, data=data, headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
    result = json.load(urllib.request.urlopen(req, timeout=30))
    if not result.get('success'):
        raise RuntimeError(result.get('msg', 'API failed'))
    return result.get('obj')

source = json.load(open('/usr/local/etc/xray/config.json'))['inbounds'][0]
existing = {x['remark'] for x in api('list')}
for name, port, transport in [('01-REALITY-Vision', 2443, 'tcp'), ('02-XHTTP-REALITY', 3443, 'xhttp')]:
    if name in existing:
        print(name, 'already exists')
        continue
    stream = copy.deepcopy(source['streamSettings'])
    stream['network'] = transport
    r = stream['realitySettings']
    keytext = subprocess.check_output(['xray', 'x25519'], text=True)
    keys = dict(line.split(': ', 1) for line in keytext.strip().splitlines())
    r['privateKey'] = keys['PrivateKey']
    r['shortIds'] = [secrets.token_hex(8)]
    r['settings'] = {'publicKey': keys['Password (PublicKey)'], 'fingerprint': 'chrome', 'serverName': r['serverNames'][0], 'spiderX': '/'}
    if transport == 'xhttp':
        stream['xhttpSettings'] = {'path': '/' + secrets.token_hex(12), 'mode': 'auto'}
    client = {'id': str(uuid.uuid4()), 'email': name.lower(), 'flow': 'xtls-rprx-vision' if transport == 'tcp' else '', 'enable': True, 'subId': secrets.token_hex(24), 'totalGB': 0, 'expiryTime': 0, 'limitIp': 0}
    inbound = {'remark': name, 'enable': True, 'port': port, 'listen': '0.0.0.0', 'protocol': 'vless', 'settings': {'clients': [client], 'decryption': 'none'}, 'streamSettings': stream, 'sniffing': {'enabled': False}, 'expiryTime': 0, 'total': 0, 'shareAddr': '77.221.138.191', 'shareAddrStrategy': 'custom'}
    api('add', inbound)
    print(name, 'created on', port)

name = '03-Hysteria2-TLS'
if name not in existing:
    client = {'auth': secrets.token_urlsafe(24), 'email': '03-hysteria2', 'enable': True, 'subId': secrets.token_hex(24), 'totalGB': 0, 'expiryTime': 0}
    stream = {'network': 'hysteria', 'security': 'tls', 'hysteriaSettings': {'version': 2}, 'tlsSettings': {'serverName': '77.221.138.191', 'alpn': ['h3'], 'minVersion': '1.3', 'certificates': [{'certificateFile': '/etc/letsencrypt/live/vpn-ip/fullchain.pem', 'keyFile': '/etc/letsencrypt/live/vpn-ip/privkey.pem'}]}}
    api('add', {'remark': name, 'enable': True, 'port': 4443, 'listen': '0.0.0.0', 'protocol': 'hysteria', 'settings': {'version': 2, 'clients': [client]}, 'streamSettings': stream, 'sniffing': {'enabled': False}, 'expiryTime': 0, 'total': 0, 'shareAddr': '77.221.138.191', 'shareAddrStrategy': 'custom'})
    print(name, 'created on 4443/udp')
