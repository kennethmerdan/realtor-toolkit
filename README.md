# 🏡 Realtor Toolkit — by Kenny Merdan · NEXA Lending

A complete content marketing & relationship platform for mortgage brokers to provide value-add services to realtor partners.

## 🚀 Features

- **📊 Dashboard** — Manage realtors, track referrals, view analytics
- **✍️ Content Studio** — AI-powered blog posts, social media, video scripts
- **📅 Content Calendar** — Schedule posts across Facebook, Instagram, TikTok, WordPress
- **🎯 Referral Tracking** — Track leads sent by realtors, calculate commissions
- **🚀 Automated Onboarding** — Set up new realtors in one click
- **🔗 Realtor Portal** — Realtors approve content before publishing
- **📱 Mobile App** — Native iOS/Android via Capacitor
- **🔗 Go High Level** — CRM sync
- **💳 Stripe Billing** — Subscription management
- **📧 Email & SMS** — Automated digests via Gmail + Twilio

## 🌐 Live Apps (after deployment)

| App | URL |
|-----|-----|
| Broker Dashboard | `https://your-app.streamlit.app` |
| Realtor Portal | `https://your-portal.streamlit.app` |
| Mobile Web | `https://your-mobile.streamlit.app` |

## 🛠️ Quick Start

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/realtor-toolkit.git
cd realtor-toolkit

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure
cp config.yaml.template config.yaml
# Edit config.yaml with your API keys

# 4. Run
streamlit run dashboard.py
```

## ☁️ Deploy to Streamlit Cloud (Free)

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **New app** → connect your GitHub repo
4. Deploy three apps:
   - `dashboard.py` → broker dashboard
   - `portal.py` → realtor portal
   - `mobile/app.py` → mobile web app
5. In each app: **Settings → Secrets** → paste your `config.yaml` contents

## 📱 Native Mobile App

```bash
cd native-app
npm install
npx cap add android
npx cap add ios
npx cap sync
```

## 🔑 API Keys Needed

| Service | Purpose | Get it at |
|---------|---------|-----------|
| OpenAI | AI content generation | platform.openai.com |
| Twilio | SMS notifications | twilio.com |
| Go High Level | CRM sync | gohighlevel.com |
| Stripe | Billing | stripe.com |
| Gmail App Password | Email digests | myaccount.google.com/apppasswords |
| Google Places | Online presence audit | console.cloud.google.com |

## 📄 License

MIT — Built by Kenny Merdan · NEXA Lending
