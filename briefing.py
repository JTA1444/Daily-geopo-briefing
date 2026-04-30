import os
import json
import smtplib
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import urllib.request

# ─────────────────────────────────────────────

# Configuration (lue depuis les secrets GitHub)

# ─────────────────────────────────────────────

GEMINI_API_KEY     = os.environ[“GEMINI_API_KEY”]
GMAIL_ADDRESS      = os.environ[“GMAIL_ADDRESS”]
GMAIL_APP_PASSWORD = os.environ[“GMAIL_APP_PASSWORD”]
RECIPIENT_EMAIL    = os.environ[“RECIPIENT_EMAIL”]

TODAY = date.today().strftime(”%A %d %B %Y”)

PROMPT = f””“Tu es un analyste géopolitique et économique de haut niveau.
Aujourd’hui nous sommes le {TODAY}.

Recherche les 5 événements géopolitiques les plus importants du jour dans le monde et analyse leur impact économique.

Réponds UNIQUEMENT avec un objet JSON valide (sans backticks, sans markdown), avec ce format exact :
{{
“headline”: “titre accrocheur résumant la journée en une phrase”,
“events”: [
{{
“flag”: “emoji drapeau du pays”,
“region”: “pays ou région”,
“title”: “titre de l’événement”,
“summary”: “résumé factuel en 2-3 phrases”,
“economic_impact”: “impact concret sur marchés, devises, matières premières ou secteurs”,
“severity”: “low|medium|high|critical”
}}
],
“market_pulse”: {{
“sentiment”: “bullish|bearish|neutral|volatile”,
“key_risks”: [“risque 1”, “risque 2”, “risque 3”],
“opportunities”: [“opportunité 1”, “opportunité 2”],
“currencies_watch”: [“USD/EUR”, “USD/JPY”]
}},
“analyst_note”: “synthèse finale en 3-4 phrases”
}}”””

SEVERITY_COLORS = {
“low”:      {“bg”: “#d1fae5”, “text”: “#065f46”, “label”: “Faible”},
“medium”:   {“bg”: “#fef3c7”, “text”: “#92400e”, “label”: “Modéré”},
“high”:     {“bg”: “#fee2e2”, “text”: “#991b1b”, “label”: “Élevé”},
“critical”: {“bg”: “#fecaca”, “text”: “#7f1d1d”, “label”: “Critique”},
}

SENTIMENT_ICONS = {
“bullish”:  (“↑”, “#065f46”),
“bearish”:  (“↓”, “#991b1b”),
“neutral”:  (“→”, “#374151”),
“volatile”: (“⚡”, “#92400e”),
}

# ─────────────────────────────────────────────

# 1. Appel API Gemini avec Google Search

# ─────────────────────────────────────────────

def fetch_briefing() -> dict:
url = (
f”https://generativelanguage.googleapis.com/v1beta/models/”
f”gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}”
)
payload = {
“contents”: [{“parts”: [{“text”: PROMPT}]}],
“tools”: [{“google_search”: {}}],   # recherche web gratuite
“generationConfig”: {“temperature”: 0.3}
}
data = json.dumps(payload).encode(“utf-8”)
req  = urllib.request.Request(
url, data=data,
headers={“Content-Type”: “application/json”},
method=“POST”
)
with urllib.request.urlopen(req) as resp:
result = json.loads(resp.read())

```
# Extraire le texte de la réponse
text = result["candidates"][0]["content"]["parts"][0]["text"]

# Nettoyer et parser le JSON
text = text.strip()
if text.startswith("```"):
    text = text.split("```")[1]
    if text.startswith("json"):
        text = text[4:]
start = text.find("{")
end   = text.rfind("}") + 1
return json.loads(text[start:end])
```

# ─────────────────────────────────────────────

# 2. Construire l’email HTML

# ─────────────────────────────────────────────

def build_html(data: dict) -> str:
sentiment_icon, sentiment_color = SENTIMENT_ICONS.get(
data[“market_pulse”][“sentiment”], (“→”, “#374151”)
)

```
events_html = ""
for ev in data.get("events", []):
    sev = SEVERITY_COLORS.get(ev.get("severity", "medium"), SEVERITY_COLORS["medium"])
    events_html += f"""
    <div style="margin-bottom:16px;padding:16px;border:1px solid #e5e7eb;
                border-left:4px solid {sev['text']};border-radius:6px;background:#fff;">
      <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
        <span style="font-size:13px;color:#6b7280;">
          {ev.get('flag','')} &nbsp;<strong>{ev.get('region','')}</strong>
        </span>
        <span style="font-size:11px;padding:2px 8px;border-radius:12px;
                     background:{sev['bg']};color:{sev['text']};font-weight:600;">
          {sev['label']}
        </span>
      </div>
      <div style="font-size:16px;font-weight:700;color:#111827;margin-bottom:8px;">
        {ev.get('title','')}
      </div>
      <div style="font-size:14px;color:#374151;line-height:1.6;margin-bottom:10px;">
        {ev.get('summary','')}
      </div>
      <div style="font-size:13px;padding:10px 14px;background:#f0fdf4;
                  border-radius:4px;color:#065f46;">
        <strong>💹 Impact :</strong> {ev.get('economic_impact','')}
      </div>
    </div>"""

risks_html = "".join(
    f'<li style="margin-bottom:6px;color:#991b1b;">{r}</li>'
    for r in data["market_pulse"].get("key_risks", [])
)
opps_html = "".join(
    f'<li style="margin-bottom:6px;color:#065f46;">{o}</li>'
    for o in data["market_pulse"].get("opportunities", [])
)
currencies_html = " &nbsp;·&nbsp; ".join(
    f'<span style="font-weight:600;">{c}</span>'
    for c in data["market_pulse"].get("currencies_watch", [])
)

return f"""<!DOCTYPE html>
```

<html lang="fr">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Briefing Géopolitique</title></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:Georgia,serif;">
<div style="max-width:640px;margin:0 auto;background:#fff;border-radius:8px;
            overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.08);">

  <div style="background:linear-gradient(135deg,#1e1b4b,#312e81);padding:28px 32px;">
    <div style="font-size:11px;letter-spacing:3px;color:#a5b4fc;text-transform:uppercase;
                margin-bottom:8px;font-family:monospace;">◈ BRIEFING QUOTIDIEN</div>
    <div style="font-size:24px;color:#fff;font-weight:normal;">{data.get('headline','')}</div>
    <div style="font-size:12px;color:#818cf8;margin-top:8px;font-family:monospace;">{TODAY}</div>
  </div>

  <div style="padding:28px 32px;">
    <div style="display:flex;gap:12px;margin-bottom:24px;flex-wrap:wrap;">
      <div style="flex:1;min-width:140px;padding:14px;border:1px solid #e5e7eb;border-radius:6px;">
        <div style="font-size:11px;color:#9ca3af;font-family:monospace;margin-bottom:4px;">SENTIMENT</div>
        <div style="font-size:20px;font-weight:bold;color:{sentiment_color};">
          {sentiment_icon} {data['market_pulse'].get('sentiment','').capitalize()}
        </div>
      </div>
      <div style="flex:2;min-width:200px;padding:14px;border:1px solid #e5e7eb;border-radius:6px;">
        <div style="font-size:11px;color:#9ca3af;font-family:monospace;margin-bottom:4px;">DEVISES À SURVEILLER</div>
        <div style="font-size:13px;color:#374151;">{currencies_html}</div>
      </div>
    </div>

```
<div style="font-size:13px;letter-spacing:2px;color:#4f46e5;text-transform:uppercase;
            font-family:monospace;margin-bottom:14px;">ÉVÉNEMENTS DU JOUR</div>
{events_html}

<div style="display:flex;gap:16px;margin-top:24px;flex-wrap:wrap;">
  <div style="flex:1;min-width:200px;">
    <div style="font-size:12px;color:#991b1b;font-family:monospace;
                letter-spacing:1px;margin-bottom:8px;">⚠ RISQUES CLÉS</div>
    <ul style="margin:0;padding-left:18px;font-size:13px;">{risks_html}</ul>
  </div>
  <div style="flex:1;min-width:200px;">
    <div style="font-size:12px;color:#065f46;font-family:monospace;
                letter-spacing:1px;margin-bottom:8px;">✦ OPPORTUNITÉS</div>
    <ul style="margin:0;padding-left:18px;font-size:13px;">{opps_html}</ul>
  </div>
</div>

<div style="margin-top:24px;padding:20px;background:#f5f3ff;
            border-left:3px solid #6366f1;border-radius:0 6px 6px 0;">
  <div style="font-size:11px;color:#6366f1;font-family:monospace;
              letter-spacing:2px;margin-bottom:8px;">◈ NOTE DE L'ANALYSTE</div>
  <div style="font-size:14px;color:#374151;line-height:1.7;font-style:italic;">
    "{data.get('analyst_note','')}"
  </div>
</div>
```

  </div>

  <div style="padding:16px 32px;background:#f9fafb;border-top:1px solid #e5e7eb;
              font-size:11px;color:#9ca3af;font-family:monospace;text-align:center;">
    Généré automatiquement par Gemini · {TODAY}
  </div>
</div>
</body></html>"""

# ─────────────────────────────────────────────

# 3. Construire le texte brut

# ─────────────────────────────────────────────

def build_text(data: dict) -> str:
lines = [
f”BRIEFING GÉOPOLITIQUE & ÉCONOMIQUE — {TODAY}”,
“=” * 60,
“”,
data.get(“headline”, “”),
“”,
f”SENTIMENT MARCHÉ : {data[‘market_pulse’].get(‘sentiment’,’’).upper()}”,
f”DEVISES : {’, ‘.join(data[‘market_pulse’].get(‘currencies_watch’, []))}”,
“”,
“─” * 60,
“ÉVÉNEMENTS DU JOUR”,
“─” * 60,
]
for i, ev in enumerate(data.get(“events”, []), 1):
lines += [
f”\n{i}. {ev.get(‘flag’,’’)} {ev.get(‘region’,’’)} — {ev.get(‘severity’,’’).upper()}”,
f”   {ev.get(‘title’,’’)}”,
f”   {ev.get(‘summary’,’’)}”,
f”   Impact : {ev.get(‘economic_impact’,’’)}”,
]
lines += [””, “─” * 60, “RISQUES CLÉS”, “─” * 60]
for r in data[“market_pulse”].get(“key_risks”, []):
lines.append(f”  ⚠ {r}”)
lines += [””, “─” * 60, “OPPORTUNITÉS”, “─” * 60]
for o in data[“market_pulse”].get(“opportunities”, []):
lines.append(f”  ✦ {o}”)
lines += [
“”, “─” * 60, “NOTE DE L’ANALYSTE”, “─” * 60,
data.get(“analyst_note”, “”),
“”, “─” * 60,
“Généré automatiquement par Gemini”,
]
return “\n”.join(lines)

# ─────────────────────────────────────────────

# 4. Envoyer l’email

# ─────────────────────────────────────────────

def send_email(html_body: str, text_body: str) -> None:
msg = MIMEMultipart(“alternative”)
msg[“Subject”] = f”📊 Briefing Géopolitique — {TODAY}”
msg[“From”]    = GMAIL_ADDRESS
msg[“To”]      = RECIPIENT_EMAIL

```
msg.attach(MIMEText(text_body, "plain", "utf-8"))
msg.attach(MIMEText(html_body, "html",  "utf-8"))

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
    server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
    server.sendmail(GMAIL_ADDRESS, RECIPIENT_EMAIL, msg.as_string())
print(f"✅ Briefing envoyé à {RECIPIENT_EMAIL}")
```

# ─────────────────────────────────────────────

# Point d’entrée

# ─────────────────────────────────────────────

if **name** == “**main**”:
print(“🔍 Récupération des événements du jour via Gemini…”)
data = fetch_briefing()
print(f”✅ {len(data.get(‘events’, []))} événements trouvés”)

```
html = build_html(data)
text = build_text(data)

print("📧 Envoi de l'email...")
send_email(html, text)
```
