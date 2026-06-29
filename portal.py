"""Realtor Portal — realtors generate & approve their own content, track referrals."""
import streamlit as st
from data_manager import DataManager


def _fallback(realtor, content_type, topic, tone, hint=""):
    loc = realtor.get('location', 'your area')
    name = realtor['name']
    if "Social" in content_type:
        return f"""🏡 {topic}

Looking to buy or sell in {loc}? I'm here to help every step of the way.

📲 DM me or call to get started!

#RealEstate #{loc.replace(' ','')} #HomeBuying #HomeSelling #Realtor"""
    elif "Blog" in content_type:
        return f"""# {topic}

*By {name} · {loc}*

Whether you're buying your first home or your fifth, navigating the real estate market in {loc} can feel overwhelming. Here's what you need to know.

## Why This Matters

The {loc} market is constantly evolving. Staying informed helps you make smarter decisions and avoid costly mistakes.

## Key Takeaways

1. **Work with a local expert** — local knowledge makes all the difference.
2. **Get pre-approved early** — it gives you a competitive edge.
3. **Don't skip the inspection** — it protects your investment.

## Ready to Take the Next Step?

I'm here to guide you through every stage of the process. Reach out today and let's talk about your goals.

*— {name}*"""
    else:  # GMB
        return f"""🏡 {topic}

{name} is here to help you navigate the {loc} real estate market with confidence.

Whether buying, selling, or investing — you deserve an expert in your corner.

📞 Call or message today to get started!"""


st.set_page_config(page_title="Realtor Portal", page_icon="🏡", layout="wide")
db = DataManager()

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("🏡 Realtor Content Portal")
st.caption("Powered by Kenny Merdan")

# ── Profile selector ───────────────────────────────────────────────────────────
realtors = db.get_all_realtors()
if not realtors:
    st.warning("No realtors in the system yet. Ask your broker to add you.")
    st.stop()

realtor_names = [f"{r['name']} — {r.get('location','N/A')}" for r in realtors]
selected = st.selectbox("Select your profile", realtor_names)
realtor = realtors[realtor_names.index(selected)]

st.divider()

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_create, tab_drafts, tab_referrals, tab_onboarding = st.tabs([
    "✨ Create Content", "📄 My Drafts", "🎯 My Referrals", "🚀 Onboarding"
])

# ── CREATE CONTENT ─────────────────────────────────────────────────────────────
with tab_create:
    st.subheader("✨ Create Content")
    st.markdown("Generate ready-to-post content for your social channels, blog, or Google Business Profile.")

    col_left, col_right = st.columns([1, 1])

    with col_left:
        content_type = st.radio(
            "What do you want to create?",
            ["📱 Social Media Post", "✍️ Blog Post", "📍 Google My Business Post"],
            help="Choose the platform you'll be posting to."
        )

        platform_map = {
            "📱 Social Media Post": "Social Media Post",
            "✍️ Blog Post": "Blog Post",
            "📍 Google My Business Post": "Google My Business Post",
        }
        content_type_clean = platform_map[content_type]

        # Platform-specific sub-options
        if content_type == "📱 Social Media Post":
            platform = st.selectbox("Platform", ["Facebook", "Instagram", "LinkedIn", "X (Twitter)"])
            topic = st.text_input("Topic or listing", placeholder="e.g. Just listed 3BR in Scottsdale, $450K")
            tone = st.selectbox("Tone", ["Friendly", "Professional", "Exciting", "Conversational"])
            extra_hint = f"Write it for {platform}. Keep it engaging and include relevant hashtags."

        elif content_type == "✍️ Blog Post":
            topic = st.text_input("Blog topic", placeholder="e.g. Top 5 tips for first-time homebuyers in 2025")
            tone = st.selectbox("Tone", ["Educational", "Professional", "Conversational", "Friendly"])
            length = st.selectbox("Length", ["Short (~300 words)", "Medium (~600 words)", "Long (~1000 words)"])
            extra_hint = f"Target length: {length}. Include a clear intro, 3-5 sections, and a call to action."

        elif content_type == "📍 Google My Business Post":
            post_type = st.selectbox("Post type", ["What's New", "Event", "Offer", "Open House"])
            topic = st.text_input("What's the post about?", placeholder="e.g. Open house this Sunday 2-4pm, 123 Main St")
            tone = st.selectbox("Tone", ["Professional", "Friendly", "Exciting"])
            extra_hint = f"This is a Google Business Profile '{post_type}' post. Keep it under 1500 characters. Include a clear call to action."

        if st.button("✨ Generate Content", type="primary", use_container_width=True):
            if not topic:
                st.warning("Please enter a topic first.")
            else:
                with st.spinner("Writing your content..."):
                    try:
                        from ai_suggestions.ai_suggester import AISuggester
                        suggester = AISuggester()
                        # Temporarily patch extra_hint into topic for richer output
                        enriched_realtor = dict(realtor)
                        content = suggester.generate_content(
                            realtor=enriched_realtor,
                            content_type=f"{content_type_clean} ({extra_hint})",
                            topic=topic,
                            tone=tone
                        )
                    except Exception:
                        content = _fallback(realtor, content_type_clean, topic, tone, extra_hint)

                    cid = db.save_content(realtor['id'], content_type_clean, topic, content)
                    st.session_state['last_content'] = content
                    st.session_state['last_topic'] = topic
                    st.success("✅ Saved to your drafts!")

    with col_right:
        st.markdown("##### Preview")
        if 'last_content' in st.session_state:
            st.markdown(st.session_state['last_content'])
            st.download_button(
                "⬇️ Download as .txt",
                data=st.session_state['last_content'],
                file_name=f"{st.session_state.get('last_topic','content')[:40]}.txt",
                mime="text/plain",
                use_container_width=True
            )
        else:
            st.info("Your generated content will appear here.")


# ── MY DRAFTS ──────────────────────────────────────────────────────────────────
with tab_drafts:
    st.subheader("📄 My Drafts")

    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        status_filter = st.selectbox("Status", ["All", "draft", "approved", "rejected"])
    with col_filter2:
        type_filter = st.selectbox("Type", ["All", "Social Media Post", "Blog Post", "Google My Business Post"])

    all_content = db.get_content(realtor_id=realtor['id'])

    # Apply filters
    filtered = [c for c in all_content
                if (status_filter == "All" or c['status'] == status_filter)
                and (type_filter == "All" or c['content_type'] == type_filter)]

    if not filtered:
        st.info("No content found.")
    else:
        st.markdown(f"**{len(filtered)} item(s)**")
        for d in filtered:
            status_emoji = {'draft': '📝', 'approved': '✅', 'rejected': '❌', 'published': '📤'}.get(d['status'], '📄')
            with st.expander(f"{status_emoji} {d['title']} · {d['content_type']} · {d['created_at'][:10]}"):
                st.markdown(d['body'])
                col1, col2, col3 = st.columns(3)
                with col1:
                    if d['status'] == 'draft':
                        if st.button("✅ Approve", key=f"app_{d['id']}", type="primary"):
                            db.update_content_status(d['id'], 'approved')
                            st.rerun()
                with col2:
                    if d['status'] == 'draft':
                        if st.button("❌ Reject", key=f"rej_{d['id']}"):
                            db.update_content_status(d['id'], 'rejected')
                            st.rerun()
                with col3:
                    st.download_button(
                        "⬇️ Download",
                        data=d['body'],
                        file_name=f"{d['title'][:40]}.txt",
                        mime="text/plain",
                        key=f"dl_{d['id']}"
                    )

# ── MY REFERRALS ───────────────────────────────────────────────────────────────
with tab_referrals:
    st.subheader("🎯 Your Referrals")
    refs = db.get_referrals(realtor_id=realtor['id'], days=90)
    funded = [r for r in refs if r['status'] == 'funded']
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Referrals (90d)", len(refs))
    col2.metric("Funded", len(funded))
    col3.metric("Commission", f"${sum(r.get('commission', 0) or 0 for r in funded):,.0f}")
    st.divider()
    if not refs:
        st.info("No referrals yet.")
    for r in refs:
        emoji = {'new': '🆕', 'contacted': '📞', 'application': '📝', 'approved': '✅', 'funded': '💰', 'lost': '❌'}.get(r['status'], '📋')
        st.markdown(f"{emoji} **{r['lead_name']}** · {r['status']} · ${r.get('loan_amount', 0):,.0f}")

# ── ONBOARDING ─────────────────────────────────────────────────────────────────
with tab_onboarding:
    st.subheader("🚀 Your Onboarding Status")
    completion = db.get_onboarding_completion(realtor['id'])
    st.progress(completion / 100, text=f"{completion:.0f}% complete")
    steps = db.get_onboarding_status(realtor['id'])
    if not steps:
        st.info("No onboarding checklist yet.")
    for step in steps:
        icon = "✅" if step['completed'] else "⏳"
        st.markdown(f"{icon} {step['description']}")
