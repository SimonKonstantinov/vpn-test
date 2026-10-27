"""Run as root on the existing VPS; stdout is SECRET. Redirect into private/ locally."""
import json
import pathlib
import sqlite3
import subprocess
import urllib.parse


def main():
    db = sqlite3.connect('file:/opt/3x-ui/db/x-ui.db?mode=ro', uri=True)
    settings = dict(db.execute('select key,value from settings'))
    subs = []
    for remark, raw in db.execute('select remark,settings from inbounds order by port'):
        for client in json.loads(raw).get('clients', []):
            if client.get('subId'):
                subs.append({'name': remark, 'url': settings.get('subURI', 'https://77.221.138.191:2096').rstrip('/') + '/' + settings.get('subPath', '').strip('/') + '/' + client['subId']})
    db.close()
    config = json.loads(pathlib.Path('/usr/local/etc/xray/config.json').read_text())
    inbound = config['inbounds'][0]
    reality = inbound['streamSettings']['realitySettings']
    keys = subprocess.check_output(['/usr/local/bin/xray', 'x25519', '-i', reality['privateKey']], text=True)
    public = next(line.split(': ', 1)[1].strip() for line in keys.splitlines() if line.startswith('Password (PublicKey):'))
    client = inbound['settings']['clients'][0]
    query = urllib.parse.urlencode({'type': 'tcp', 'security': 'reality', 'pbk': public, 'fp': 'chrome', 'sni': reality['serverNames'][0], 'sid': reality['shortIds'][0], 'flow': client.get('flow', '')})
    link = 'vless://' + client['id'] + '@77.221.138.191:' + str(inbound['port']) + '?' + query + '#CompassVPN-04-REALITY-443'
    print(json.dumps({'grafana_user': 'admin', 'grafana_password': pathlib.Path('/opt/vpn-monitoring/grafana_admin_password').read_text().strip(), 'panel_access': pathlib.Path('/opt/3x-ui/admin-access.txt').read_text(), 'subscriptions': subs, 'variant_04_uri': link}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
