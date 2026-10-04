# Navbatchi Bot

Kvartiradagi navbatchilikni har kuni soat **07:00** va **19:00**da (Toshkent vaqti) guruhga eslatadigan Telegram bot.

## Qanday ishlaydi

- `storage.py` dagi `data/state.json` faylida 8 kishilik ro'yxat va "boshlanish sanasi" saqlanadi.
- Har kuni kim navbatchi ekani sanadan avtomatik hisoblanadi (aylanma tartibda), hech qanday qo'lda belgilash kerak emas.
- Ertalab va kechqurun bot `/belgila` orqali belgilangan guruhga xabar yuboradi.

## Buyruqlar

- `/bugun` — bugungi navbatchi
- `/ertaga` — ertangi navbatchi
- `/kecha` — kechagi navbatchi
- `/royxat` — barcha navbatchilar ro'yxati
- `/haftalik` — keyingi 7 kunlik jadval
- `/belgila` — shu guruhni eslatmalar uchun belgilash (faqat guruh adminlari ishlatadi)

## Lokal ishga tushirish (test uchun)

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

`.env` faylini yaratib, ichiga botning tokenini yozing (`.env.example` ga qarang):

```
BOT_TOKEN=...
```

So'ng ishga tushiring:

```powershell
.\.venv\Scripts\python bot.py
```

Botni test guruhga qo'shing, admin qiling (yoki kamida xabar yozish huquqini bering), va guruhda `/belgila` deb yozing — shundan keyin bot shu guruhga eslatma yubora boshlaydi.

> **Eslatma:** Bot keyingi marta ishga tushirilganda ham guruh eslab qolinadi (`data/state.json` ga yoziladi), qayta `/belgila` yozish shart emas — faqat guruhni almashtirmoqchi bo'lsangiz kerak bo'ladi.

## Doimiy ishlashi uchun (kompyuterga bog'liq bo'lmasligi)

Bot kompyuteringiz o'chirilganda yoki VS Code yopilganda ham ishlashi uchun uni **serverga** joylashtirish kerak. Variantlar:

### 1-variant: Arzon VPS (eng ishonchli, tavsiya qilinadi)

Masalan Hetzner, DigitalOcean, Timeweb kabi xizmatlardan oyiga ~3-5$ turadigan kichik VPS (Ubuntu) oling, so'ng:

```bash
git clone <repo> navbatchi-bot   # yoki fayllarni serverga ko'chiring
cd navbatchi-bot
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
```

`.env` faylini serverda qo'lda yarating (tokenni shunday joylang), so'ng doimiy ishlashi uchun systemd xizmat qiling:

`/etc/systemd/system/navbatchi-bot.service`:

```ini
[Unit]
Description=Navbatchi Telegram Bot
After=network.target

[Service]
WorkingDirectory=/root/navbatchi-bot
ExecStart=/root/navbatchi-bot/.venv/bin/python bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now navbatchi-bot
sudo systemctl status navbatchi-bot
```

Shu bilan bot server qayta yoqilsa ham, xatolik bo'lsa ham o'zi qayta ishga tushadi.

### 2-variant: Railway / Fly.io (bulutli, kartasiz boshlab ko'rish mumkin)

Repo ichida `Dockerfile` va `Procfile` tayyor:

- **Railway**: loyihani GitHub'ga joylang, Railway'da "New Project → Deploy from GitHub", `BOT_TOKEN` ni Variables bo'limiga qo'shing. Railway avtomatik `Dockerfile`dan foydalanadi.
- **Fly.io**: `flyctl launch` (HTTP porti kerak emas, "no services" tanlang), `flyctl secrets set BOT_TOKEN=...`, so'ng `flyctl deploy`.

> Diqqat: bulut platformalarida konteyner qayta tiklanganda `data/state.json` fayli yo'qolib qolishi mumkin (agar doimiy disk/volume ulamasangiz). Shuning uchun VPS + systemd eng barqaror variant.

## Xavfsizlik bo'yicha eslatma

Bot tokeni ushbu suhbatda ochiq yuborilgan edi — token `.env` fayliga yozib qo'yildi va `.gitignore` orqali Git'ga tushmaydi. Agar loyihani biror joyga (GitHub va h.k.) yuklasangiz, tasodifan tokenni commit qilib yubormaslik uchun ehtiyot bo'ling. Xavfsizlik uchun tavsiya: @BotFather'da `/revoke` orqali eski tokenni bekor qilib, yangi token oling va uni faqat `.env` ichida saqlang.
