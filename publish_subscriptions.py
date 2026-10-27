import os
import pathlib
import sqlite3
import subprocess
import time

root = pathlib.Path('/opt/3x-ui')
os.umask(0o077)
if not (root / 'db/x-ui.db').is_file():
    raise RuntimeError('Existing initialized 3x-ui database required')
if not pathlib.Path('/etc/letsencrypt/live/vpn-ip/fullchain.pem').is_file():
    raise RuntimeError('Existing vpn-ip certificate required')
subprocess.run(['docker', 'stop', 'vpn-3x-ui'], check=True, stdout=subprocess.DEVNULL)
try:
    db = sqlite3.connect(root / 'db/x-ui.db')
    backup = sqlite3.connect(root / ('db/backup-before-sub-' + str(int(time.time())) + '.db'))
    db.backup(backup)
    backup.close()
    settings = {'subEnable': 'true', 'subPort': '2096', 'subListen': '0.0.0.0', 'subCertFile': '/etc/letsencrypt/live/vpn-ip/fullchain.pem', 'subKeyFile': '/etc/letsencrypt/live/vpn-ip/privkey.pem', 'subURI': 'https://77.221.138.191:2096', 'subEncrypt': 'true', 'subTitle': 'CompassVPN | {{EMAIL}}'}
    for k, v in settings.items():
        if db.execute('select 1 from settings where key=?', (k,)).fetchone():
            db.execute('update settings set value=? where key=?', (v,k))
        else:
            db.execute('insert into settings(key,value) values(?,?)', (k,v))
    db.commit()
    db.close()
    (root / 'compose.yml').write_text('''services:
      panel:
        image: ghcr.io/mhsanaei/3x-ui@sha256:1628adbd9bed680d25d6f714bef4a20f132105f4612ea294952f6665dad32e5b
        container_name: vpn-3x-ui
        restart: unless-stopped
        environment:
          XUI_ENABLE_FAIL2BAN: "false"
        ports:
          - "127.0.0.1:2053:2053"
          - "2096:2096"
          - "2443:2443"
          - "3443:3443"
          - "4443:4443/udp"
        volumes:
          - /opt/3x-ui/db:/etc/x-ui
          - /etc/letsencrypt:/etc/letsencrypt:ro
    ''')
finally:
    subprocess.run(['docker','start','vpn-3x-ui'], check=True, stdout=subprocess.DEVNULL)
subprocess.run(['docker','compose','-f',str(root/'compose.yml'),'up','-d'],check=True)
pathlib.Path('/etc/systemd/system/vpn-ip-renew.service').write_text('''[Unit]
Description=Renew IP certificate for VPN subscriptions
[Service]
Type=oneshot
ExecStart=/opt/certbot-ip/bin/certbot renew --quiet --cert-name vpn-ip --deploy-hook "docker restart vpn-3x-ui"
''')
pathlib.Path('/etc/systemd/system/vpn-ip-renew.timer').write_text('''[Unit]
Description=Check VPN IP certificate twice daily
[Timer]
OnCalendar=*-*-* 00,12:00:00
RandomizedDelaySec=3600
Persistent=true
[Install]
WantedBy=timers.target
''')
subprocess.run(['systemctl','daemon-reload'],check=True)
subprocess.run(['systemctl','enable','--now','vpn-ip-renew.timer'],check=True)
subprocess.run(['systemctl','disable','--now','certbot.timer'],check=True)
print('HTTPS subscriptions published; panel stays on loopback; renewal timer enabled.')
