# Инструкция для владельца и проверяющего

## 1. Войти в Grafana и 3x-ui с Windows

Откройте PowerShell и вставьте **одной строкой**:

```powershell
ssh -i "$env:USERPROFILE\.ssh\codex_vps_key" -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -N -L 3000:127.0.0.1:3000 -L 2053:127.0.0.1:2053 ansible@77.221.138.191
```

Окно оставьте открытым. Отсутствие текста при работающем туннеле нормально. Откройте:

- Grafana: http://127.0.0.1:3000 — логин `admin`, пароль в локальном `private/ACCESS.txt`. Dashboards → CompassVPN → CompassVPN Dashboard.
- 3x-ui: http://127.0.0.1:2053/panel/ — логин и пароль в том же файле.

Остановить туннель: Ctrl+C. Если порт занят, закройте прежний туннель либо замените первый `3000` на `13000` и откройте http://127.0.0.1:13000. Проверяющему нужен собственный разрешённый SSH-ключ; копирование команды без ключа доступа не даст.

Альтернатива из папки проекта:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Open-CompassVPN.ps1
```

## 2. Подключиться к серверной консоли

```powershell
ssh -i "$env:USERPROFILE\.ssh\codex_vps_key" ansible@77.221.138.191
```

Внутри Linux проверить службы:

```bash
systemctl status xray --no-pager
sudo docker ps
systemctl status vpn-ip-renew.timer --no-pager
sudo journalctl -u vpn-ip-renew.service -n 30 --no-pager
```

`up` у контейнера или `active` у службы не доказывает соединение клиента.

## 3. Создать и скачать свежий понятный отчёт одной командой

Из папки проекта в PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Get-VpnReport.ps1
```

Скрипт запускает `/home/ansible/vpn-test/report.yml`, проверяет код завершения, скачивает HTML и JSON в Downloads и открывает HTML. Старый поиск файлов по `*.md` больше не используется. HTML содержит статус службы, контейнеры, доступность внешних HTTPS-сайтов с VPS, Grafana, Prometheus и срок сертификата. Это серверный отчёт, не тест клиентских утечек.

При переносе на другой VPS сначала загрузите проект:

```powershell
scp -i "$env:USERPROFILE\.ssh\codex_vps_key" report.yml ansible@77.221.138.191:/home/ansible/vpn-test/report.yml
```

Каталог назначения должен существовать. На текущем VPS подготовленный комплект расположен в `/home/ansible/vpn-test`.

## 4. Playbook: порядок и ограничения

Все playbook исполняются **на Linux VPS**. Нужны Ubuntu, sudo, Ansible, Python3, Docker для панели/мониторинга. Ansible 2.20 проверялся на текущем сервере. Запуск с `-i localhost, -c local` намеренно локальный; не запускайте deployment-playbook на своём ПК.

```bash
cd /home/ansible/vpn-test
ansible-playbook -i localhost, -c local discover.yml
sudo ansible-playbook -i localhost, -c local report.yml
```

Изменяющие конфигурацию команды запускаются отдельно по необходимости:

```bash
sudo ansible-playbook -i localhost, -c local site.yml
sudo ansible-playbook -i localhost, -c local monitoring.yml
sudo ansible-playbook -i localhost, -c local subscriptions.yml
```

- `site.yml` сохраняет существующий config. Для нового config нужны свободный 443 и доступ к официальному Xray installer на GitHub. Installer загружается из main; для строго воспроизводимого production-развёртывания необходимо зафиксировать его ревизию и контрольную сумму. Существующая установка не обновляется автоматически.
- `monitoring.yml` использует Docker Compose; версии образов соответствуют стенду. Данные хранятся в named volumes. Пароль создаётся один раз. Изменение файла начального пароля не сбрасывает уже установленный пароль Grafana.
- `subscriptions.yml` требует существующие `/opt/3x-ui/db/x-ui.db`, `/usr/local/etc/xray/config.json`, сертификат `vpn-ip`, `/opt/certbot-ip/bin/certbot`. Это обслуживание установленного стенда, не первичная установка панели. Имена контейнера и образ зафиксированы; перед переносом изучить Python-скрипт публикации. Повторное выполнение перезапускает панель.
- `create_test_inbounds.py` определяет наличие профиля по remark; изменённый вручную существующий профиль автоматически не исправляется.

В standalone-конфигурации Certbot 5.8 выдача IP-сертификата выполнялась следующей командой. Повторять её на действующем VPS ради проверки не требуется:

```bash
sudo /opt/certbot-ip/bin/certbot certonly --standalone --preferred-profile shortlived --ip-address 77.221.138.191 --cert-name vpn-ip --non-interactive --agree-tos --register-unsafely-without-email
```

Первичная панель ранее была инициализирована отдельно; база с клиентами и приватные ключи не входят в GitHub. Развёртывание с нуля из этого комплекта не проверено.

## 5. Подписки и повторение проверки

На ПК и Android в Happ добавьте отдельные URL №01–03 из `private/ACCESS.txt`; для №04 импортируйте прямую VLESS-ссылку. Последовательно включайте ровно один профиль. Для Android отдельно повторите Wi-Fi и мобильную сеть с отключённым Wi-Fi. Зафиксируйте открытие api.ipify.org, YouTube, время UTC и журнал ошибок. Название №03 в логах может содержать `hysteria`, хотя это версия 2.

На ПК скриптовый SOCKS-тест первых трёх подписок запускается из PowerShell:

```powershell
& .\Test-VpnSubscriptions.ps1 -Links (Get-Content -Raw .\private\subscriptions.json | ConvertFrom-Json)
```

Нужны Happ с ядром по пути `C:\Program Files\FlyFrogLLC\Happ\core\xray.exe`, curl.exe и свободный порт 19081. Скрипт пишет локальные журналы и JSON, удаляет временный config, не включает системный TUN. Для независимого опыта отключите другие VPN до запуска. Стандартный тест принимает одноузловые base64-подписки этого стенда, не произвольные форматы.

## 6. Резервные копии и откат

Перед изменениями сохраните root-only копии `/usr/local/etc/xray/config.json`, `/opt/3x-ui/db`, `/opt/3x-ui/compose.yml`, `/opt/vpn-monitoring` и Docker volumes. БД панели копировать при остановленной панели либо SQLite backup API. Копии содержат ключи и пароли, не добавляйте в git.

Скрипт публикации создаёт `backup-before-sub-<timestamp>.db` до изменения настроек. Для отката остановите `vpn-3x-ui`, восстановите выбранную БД и прежний compose, затем запустите compose. Не запускайте одновременно старый rollback-контейнер и текущую панель с одной БД. Откат не выполнен в рамках подготовки отчёта.

## 7. Передача на проверку

Передайте ссылку на репозиторий и `docs/REPORT.html`. Пароли и подписки из `private/ACCESS.txt` передавайте отдельно по согласованному закрытому каналу. SSH private key отсутствует в комплекте. Не публикуйте полный вывод collect_access.py, необработанные client logs или БД панели.
