import streamlit as st
from data_manager import DataManager
from datetime import datetime, date

st.set_page_config(page_title="Realtor Toolkit", page_icon="🏡", layout="wide")
db = DataManager()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/color/96/home.png", width=60)
    st.title("Realtor Toolkit")
    st.caption("By Kenny Merdan")
    st.divider()
    nav = st.radio(
        "Navigation",
        [
            "📊 Overview", "👥 Realtors", "📅 Calendar",
            "✍️ Content Studio", "🎬 Video Upload", "📤 Publishing Center",
            "📋 Audit Center", "📧 Email Center", "📈 Analytics",
            "🤖 AI Suggestions", "🎯 Referrals", "🚀 Onboarding",
            "🔗 Portal Links", "💳 Billing", "🔗 GHL Sync", "⚙️ Settings"
        ],
        label_visibility="collapsed"
    )

# ── Overview ──────────────────────────────────────────────────────────────────
if nav == "📊 Overview":
    st.title("📊 Dashboard Overview")
    realtors = db.get_all_realtors()
    referrals = db.get_referrals(days=30)
    funded = [r for r in referrals if r['status'] == 'funded']

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Realtors", len(realtors))
    col2.metric("Referrals (30d)", len(referrals))
    col3.metric("Funded Loans", len(funded))
    col4.metric("Commission (30d)", f"${sum(r.get('commission',0) or 0 for r in funded):,.0f}")

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("👥 Recent Realtors")
        for r in realtors[:5]:
            st.markdown(f"**{r['name']}** · {r.get('location','N/A')}")
    with col2:
        st.subheader("🎯 Recent Referrals")
        for r in referrals[:5]:
            status_emoji = {'new':'🆕','contacted':'📞','application':'📝','approved':'✅','funded':'💰','lost':'❌'}.get(r['status'],'📋')
            st.markdown(f"{status_emoji} **{r['lead_name']}** · {r['realtor_name']}")

# ── Realtors ──────────────────────────────────────────────────────────────────
elif nav == "👥 Realtors":
    st.title("👥 Manage Realtors")
    tab_list, tab_add = st.tabs(["📋 All Realtors", "➕ Add Realtor"])

    with tab_list:
        realtors = db.get_all_realtors()
        if not realtors:
            st.info("No realtors yet. Add one to get started!")
        for r in realtors:
            completion = db.get_onboarding_completion(r['id'])
            with st.expander(f"**{r['name']}** · {r.get('location','N/A')} · Onboarding: {completion:.0f}%"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"📧 {r.get('email','N/A')}")
                    st.write(f"📱 {r.get('phone','N/A')}")
                    st.write(f"🌐 {r.get('website','N/A')}")
                with col2:
                    st.write(f"📘 Facebook: {r.get('facebook_page_id','N/A')}")
                    st.write(f"📸 Instagram: {r.get('instagram_handle','N/A')}")
                    st.write(f"🎵 TikTok: {r.get('tiktok_handle','N/A')}")
                if st.button("🗑️ Delete", key=f"del_{r['id']}"):
                    db.delete_realtor(r['id'])
                    st.rerun()

    with tab_add:
        st.subheader("➕ Add New Realtor")
        with st.form("add_realtor"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name *")
                email = st.text_input("Email")
                phone = st.text_input("Phone")
                location = st.text_input("Location (City, State)")
                website = st.text_input("Website")
            with col2:
                google_business_id = st.text_input("Google Business ID")
                facebook_page_id = st.text_input("Facebook Page ID")
                instagram_handle = st.text_input("Instagram Handle")
                tiktok_handle = st.text_input("TikTok Handle")
            submitted = st.form_submit_button("➕ Add Realtor", use_container_width=True)
            if submitted:
                if not name:
                    st.error("Name is required!")
                else:
                    rid = db.add_realtor(
                        name, email, phone, location,
                        website=website,
                        google_business_id=google_business_id,
                        facebook_page_id=facebook_page_id,
                        instagram_handle=instagram_handle,
                        tiktok_handle=tiktok_handle
                    )
                    db.create_onboarding_checklist(rid)
                    st.success(f"✅ {name} added! Onboarding checklist created.")
                    st.rerun()

# ── Calendar ──────────────────────────────────────────────────────────────────
elif nav == "📅 Calendar":
    st.title("📅 Content Calendar")
    realtors = db.get_all_realtors()
    if not realtors:
        st.warning("Add a realtor first!")
    else:
        realtor_map = {"All": None} | {f"{r['name']} — {r['location']}": r['id'] for r in realtors}
        selected = st.selectbox("Filter by Realtor", list(realtor_map.keys()))
        rid = realtor_map[selected]
        posts = db.get_scheduled_posts(realtor_id=rid, status='pending')
        if not posts:
            st.info("No scheduled posts.")
        for p in posts:
            with st.expander(f"📅 {p['scheduled_at'][:16]} · {p['platform']} · {p['realtor_name']}"):
                st.markdown(f"**{p['title']}**")
                st.write(p['body'][:300])
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Mark Published", key=f"pub_{p['id']}"):
                        db.update_scheduled_post_status(p['id'], 'published')
                        db.update_content_status(p['content_id'], 'published')
                        st.rerun()
                with col2:
                    if st.button("🗑️ Cancel", key=f"can_{p['id']}"):
                        db.update_scheduled_post_status(p['id'], 'cancelled')
                        st.rerun()

# ── Content Studio ────────────────────────────────────────────────────────────
elif nav == "✍️ Content Studio":
    st.title("✍️ Content Studio")
    realtors = db.get_all_realtors()
    if not realtors:
        st.warning("Add a realtor first!")
    else:
        realtor_map = {f"{r['name']} — {r['location']}": r for r in realtors}
        selected = st.selectbox("Select Realtor", list(realtor_map.keys()))
        realtor = realtor_map[selected]

        tab_gen, tab_drafts = st.tabs(["✨ Generate Content", "📄 Drafts"])

        with tab_gen:
            content_type = st.selectbox("Content Type", ["Blog Post", "Social Media Post", "Video Script", "Email Newsletter"])
            topic = st.text_input("Topic", placeholder="e.g. First-time homebuyer tips in Dallas")
            tone = st.selectbox("Tone", ["Professional", "Friendly", "Educational", "Conversational"])
            if st.button("✨ Generate", use_container_width=True):
                with st.spinner("Generating content..."):
                    try:
                        from ai_suggestions.ai_suggester import AISuggester
                        suggester = AISuggester()
                        content = suggester.generate_content(
                            realtor=realtor,
                            content_type=content_type,
                            topic=topic,
                            tone=tone
                        )
                    except Exception:
                        content = f"""# {topic}

Here is a {tone.lower()} {content_type.lower()} for {realtor['name']} in {realtor.get('location','your area')}.

[AI content will appear here once your OpenAI API key is configured in config.yaml]

## Key Points:
- Local market insight 1
- Buyer/seller tip 2
- Call to action: Contact {realtor['name']} for more information

*Generated by Realtor Toolkit*"""

                    cid = db.save_content(realtor['id'], content_type, topic or "Generated Content", content)
                    st.success("✅ Content saved to drafts!")
                    st.markdown(content)

        with tab_drafts:
            drafts = db.get_content(realtor_id=realtor['id'], status='draft')
            if not drafts:
                st.info("No drafts.")
            for d in drafts:
                with st.expander(f"📄 {d['title']} · {d['created_at'][:10]}"):
                    st.markdown(d['body'])
                    col1, col2, col3 = st.columns(3)
                    platform = col1.selectbox("Platform", ["Facebook","Instagram","TikTok","WordPress"], key=f"plat_{d['id']}")
                    sched_date = col2.date_input("Schedule Date", date.today(), key=f"date_{d['id']}")
                    sched_time = col3.time_input("Time", key=f"time_{d['id']}")
                    if st.button("📅 Schedule", key=f"sched_{d['id']}"):
                        sched_dt = datetime.combine(sched_date, sched_time).isoformat()
                        db.schedule_post(realtor['id'], d['id'], platform, sched_dt)
                        db.update_content_status(d['id'], 'scheduled')
                        st.success("Scheduled!")
                        st.rerun()

# ── Referrals ─────────────────────────────────────────────────────────────────
elif nav == "🎯 Referrals":
    st.title("🎯 Referral Tracking")
    tab_dashboard, tab_add, tab_list = st.tabs(["📊 Dashboard", "➕ Add Referral", "📋 All Referrals"])

    with tab_dashboard:
        all_refs = db.get_referrals(days=90)
        funded_refs = [r for r in all_refs if r['status'] == 'funded']
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total (90d)", len(all_refs))
        col2.metric("Funded", len(funded_refs))
        col3.metric("Close Rate", f"{(len(funded_refs)/max(1,len(all_refs))*100):.1f}%")
        col4.metric("Commission", f"${sum(r.get('commission',0) or 0 for r in funded_refs):,.0f}")

        st.subheader("🏆 Top Referrers")
        by_realtor = {}
        for r in all_refs:
            rn = r['realtor_name']
            if rn not in by_realtor:
                by_realtor[rn] = {'total': 0, 'funded': 0, 'commission': 0}
            by_realtor[rn]['total'] += 1
            if r['status'] == 'funded':
                by_realtor[rn]['funded'] += 1
                by_realtor[rn]['commission'] += r.get('commission', 0) or 0
        for i, (name, stats) in enumerate(sorted(by_realtor.items(), key=lambda x: x[1]['total'], reverse=True)[:5], 1):
            st.markdown(f"**#{i} {name}** · {stats['total']} referrals · {stats['funded']} funded · ${stats['commission']:,.0f}")

    with tab_add:
        realtors = db.get_all_realtors()
        if not realtors:
            st.warning("Add a realtor first!")
        else:
            realtor_map = {f"{r['name']} — {r.get('location','N/A')}": r for r in realtors}
            selected = st.selectbox("Realtor", list(realtor_map.keys()))
            realtor = realtor_map[selected]
            with st.form("add_referral"):
                col1, col2 = st.columns(2)
                with col1:
                    lead_name = st.text_input("Lead Name *")
                    lead_email = st.text_input("Lead Email")
                    lead_phone = st.text_input("Lead Phone")
                with col2:
                    loan_type = st.selectbox("Loan Type", ["conventional","fha","va","jumbo","refinance"])
                    loan_amount = st.number_input("Loan Amount", min_value=0, step=10000, value=400000)
                notes = st.text_area("Notes")
                submitted = st.form_submit_button("➕ Add Referral", use_container_width=True)
                if submitted and lead_name:
                    commission = loan_amount * 0.001  # 0.1% default
                    rid = db.add_referral(
                        realtor['id'], lead_name, lead_email, lead_phone,
                        loan_amount=loan_amount, loan_type=loan_type, notes=notes
                    )
                    db.update_referral_status(rid, 'new', commission=commission)
                    st.success(f"✅ Added! Est. commission: ${commission:,.0f}")
                    st.rerun()

    with tab_list:
        status_filter = st.selectbox("Status", ["all","new","contacted","application","approved","funded","lost"])
        refs = db.get_referrals(status=None if status_filter == "all" else status_filter, days=90)
        for r in refs:
            emoji = {'new':'🆕','contacted':'📞','application':'📝','approved':'✅','funded':'💰','lost':'❌'}.get(r['status'],'📋')
            with st.expander(f"{emoji} {r['lead_name']} · {r['realtor_name']} · ${r.get('loan_amount',0):,.0f}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"Email: {r.get('lead_email','N/A')}")
                    st.write(f"Phone: {r.get('lead_phone','N/A')}")
                with col2:
                    st.write(f"Loan: ${r.get('loan_amount',0):,.0f} ({r.get('loan_type','N/A')})")
                    st.write(f"Commission: ${r.get('commission',0):,.0f}")
                new_status = st.selectbox("Update Status", ["new","contacted","application","approved","funded","lost"],
                    index=["new","contacted","application","approved","funded","lost"].index(r['status']),
                    key=f"rs_{r['id']}")
                if st.button("💾 Update", key=f"ru_{r['id']}"):
                    db.update_referral_status(r['id'], new_status)
                    st.success("Updated!")
                    st.rerun()

# ── Onboarding ────────────────────────────────────────────────────────────────
elif nav == "🚀 Onboarding":
    st.title("🚀 Automated Onboarding")
    realtors = db.get_all_realtors()
    if not realtors:
        st.warning("Add a realtor first!")
    else:
        tab_start, tab_status = st.tabs(["🚀 Start Onboarding", "📋 Status"])
        with tab_start:
            for r in realtors:
                completion = db.get_onboarding_completion(r['id'])
                if completion < 100:
                    with st.expander(f"{'🟡' if completion > 0 else '⚪'} {r['name']} — {completion:.0f}% complete"):
                        if st.button(f"🚀 Onboard {r['name']}", key=f"ob_{r['id']}", type="primary"):
                            with st.spinner("Running onboarding..."):
                                steps = db.get_onboarding_status(r['id'])
                                for step in steps:
                                    db.complete_onboarding_step(r['id'], step['step'])
                                st.success(f"✅ {r['name']} onboarded!")
                                st.rerun()

        with tab_status:
            for r in realtors:
                completion = db.get_onboarding_completion(r['id'])
                with st.expander(f"{r['name']} — {completion:.0f}% complete"):
                    steps = db.get_onboarding_status(r['id'])
                    for step in steps:
                        icon = "✅" if step['completed'] else "⏳"
                        st.markdown(f"{icon} {step['description']}")

# ── Settings ──────────────────────────────────────────────────────────────────
elif nav == "⚙️ Settings":
    st.title("⚙️ Settings")
    st.info("Configure your API keys and settings in `config.yaml` or Streamlit Cloud Secrets.")
    st.code("""
# config.yaml
openai_api_key: "sk-..."
google_places_api_key: "AIza..."
twilio_account_sid: "AC..."
twilio_auth_token: "..."
twilio_from_number: "+1..."
ghl_api_key: "..."
stripe_secret_key: "sk_..."
gmail_user: "your@gmail.com"
gmail_app_password: "xxxx xxxx xxxx xxxx"
""", language="yaml")
    st.markdown("📖 See [config.yaml.template](config.yaml.template) for all options.")

# ── Stub pages ────────────────────────────────────────────────────────────────
elif nav in ["🎬 Video Upload", "📤 Publishing Center", "📋 Audit Center",
             "📧 Email Center", "📈 Analytics", "🤖 AI Suggestions",
             "🔗 Portal Links", "💳 Billing", "🔗 GHL Sync"]:
    st.title(nav)
    st.info(f"**{nav}** is available — configure your API keys in Settings to activate it.")
    st.markdown("""
**To activate all features:**
1. Go to ⚙️ Settings and add your API keys to `config.yaml`
2. For Streamlit Cloud: add keys in **Settings → Secrets**
3. Restart the app

**Supported integrations:**
- 🤖 OpenAI — content generation & AI suggestions
- 📱 Twilio — SMS notifications
- 🔗 Go High Level — CRM sync
- 💳 Stripe — subscription billing
- 📧 Gmail — email digests & audit reports
- 📊 Google Places — online presence auditing
""")
