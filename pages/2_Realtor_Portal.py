"""Realtor Portal - realtors generate and approve content."""
import streamlit as st
from data_manager import DataManager


def fallback_content(realtor, content_type, topic, tone):
    loc = realtor.get('location', 'your area')
    name = realtor['name']
    tag = loc.replace(' ', '')
    if "Social" in content_type:
        lines = [
            f"Thinking about buying or selling in {loc}?",
            f"Now is a great time to make your move!",
            f"",
            f"{topic}",
            f"",
            f"DM me or call today to get started.",
            f"",
            f"#RealEstate #{tag} #HomeBuying #HomeSelling #Realtor",
        ]
        return "\n".join(lines)
    elif "Blog" in content_type:
        lines = [
            f"# {topic}",
            f"",
            f"*By {name} - {loc}*",
            f"",
            f"Navigating the real estate market in {loc} can feel overwhelming. Here is what you need to know.",
            f"",
            f"## Why This Matters",
            f"",
            f"The {loc} market is constantly evolving. Staying informed helps you make smarter decisions.",
            f"",
            f"## Key Takeaways",
            f"",
            f"1. Work with a local expert - local knowledge makes all the difference.",
            f"2. Get pre-approved early - it gives you a competitive edge.",
            f"3. Do not skip the inspection - it protects your investment.",
            f"",
            f"## Ready to Take the Next Step?",
            f"",
            f"Reach out today and let's talk about your goals.",
            f"",
            f"*-- {name}*",
        ]
        return "\n".join(lines)
    else:
        lines = [
            f"{topic}",
            f"",
            f"{name} is here to help you navigate the {loc} real estate market.",
            f"",
            f"Whether buying, selling, or investing - you deserve an expert in your corner.",
            f"",
            f"Call or message today to get started!",
        ]
        return "\n".join(lines)


st.set_page_config(page_title="Realtor Portal", page_icon="🏡", layout="wide")
db = DataManager()

st.title("Realtor Content Portal")
st.caption("Powered by Kenny Merdan")

realtors = db.get_all_realtors()
if not realtors:
    st.warning("No realtors in the system yet. Ask your broker to add you.")
    st.stop()

realtor_names = [f"{r['name']} -- {r.get('location', 'N/A')}" for r in realtors]
selected = st.selectbox("Select your profile", realtor_names)
realtor = realtors[realtor_names.index(selected)]

st.divider()

tab_create, tab_drafts, tab_refs, tab_onboard = st.tabs([
    "Create Content", "My Drafts", "My Referrals", "Onboarding"
])

# ── CREATE CONTENT ─────────────────────────────────────────────────────────────
with tab_create:
    st.subheader("Create Content")
    st.caption("Generate ready-to-post content for social, your blog, or Google Business Profile.")

    col_left, col_right = st.columns([1, 1])

    with col_left:
        content_type = st.radio(
            "Content type",
            ["Social Media Post", "Blog Post", "Google My Business Post"]
        )
        topic = st.text_input("Topic", placeholder="e.g. Tips for first-time buyers in Scottsdale")
        tone = st.selectbox("Tone", ["Friendly", "Professional", "Educational", "Exciting"])

        if content_type == "Social Media Post":
            platform = st.selectbox("Platform", ["Facebook", "Instagram", "LinkedIn", "X (Twitter)"])
        elif content_type == "Blog Post":
            length = st.selectbox("Length", ["Short (~300 words)", "Medium (~600 words)", "Long (~1000 words)"])
        else:
            post_type = st.selectbox("Post type", ["What's New", "Event", "Offer", "Open House"])

        if st.button("Generate Content", type="primary", use_container_width=True):
            if not topic:
                st.warning("Please enter a topic first.")
            else:
                with st.spinner("Writing your content..."):
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
                        content = fallback_content(realtor, content_type, topic, tone)
                    db.save_content(realtor['id'], content_type, topic, content)
                    st.session_state['last_content'] = content
                    st.session_state['last_topic'] = topic
                    st.success("Saved to your drafts!")

    with col_right:
        st.markdown("**Preview**")
        if 'last_content' in st.session_state:
            st.markdown(st.session_state['last_content'])
            st.download_button(
                "Download .txt",
                data=st.session_state['last_content'],
                file_name=f"{st.session_state.get('last_topic','content')[:40]}.txt",
                mime="text/plain",
                use_container_width=True
            )
        else:
            st.info("Your generated content will appear here.")

# ── MY DRAFTS ──────────────────────────────────────────────────────────────────
with tab_drafts:
    st.subheader("My Drafts")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        status_filter = st.selectbox("Status", ["All", "draft", "approved", "rejected"])
    with col_f2:
        type_filter = st.selectbox("Type", ["All", "Social Media Post", "Blog Post", "Google My Business Post"])

    all_content = db.get_content(realtor_id=realtor['id'])
    filtered = [
        c for c in all_content
        if (status_filter == "All" or c['status'] == status_filter)
        and (type_filter == "All" or c['content_type'] == type_filter)
    ]

    if not filtered:
        st.info("No content found.")
    else:
        st.markdown(f"**{len(filtered)} item(s)**")
        for d in filtered:
            s_emoji = {'draft': 'DRAFT', 'approved': 'APPROVED', 'rejected': 'REJECTED'}.get(d['status'], d['status'])
            with st.expander(f"{s_emoji}: {d['title']} | {d['content_type']} | {d['created_at'][:10]}"):
                st.markdown(d['body'])
                c1, c2, c3 = st.columns(3)
                with c1:
                    if d['status'] == 'draft':
                        if st.button("Approve", key=f"app_{d['id']}", type="primary"):
                            db.update_content_status(d['id'], 'approved')
                            st.rerun()
                with c2:
                    if d['status'] == 'draft':
                        if st.button("Reject", key=f"rej_{d['id']}"):
                            db.update_content_status(d['id'], 'rejected')
                            st.rerun()
                with c3:
                    st.download_button(
                        "Download",
                        data=d['body'],
                        file_name=f"{d['title'][:40]}.txt",
                        mime="text/plain",
                        key=f"dl_{d['id']}"
                    )

# ── MY REFERRALS ───────────────────────────────────────────────────────────────
with tab_refs:
    st.subheader("Your Referrals")
    refs = db.get_referrals(realtor_id=realtor['id'], days=90)
    funded = [r for r in refs if r['status'] == 'funded']
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Referrals (90d)", len(refs))
    c2.metric("Funded", len(funded))
    c3.metric("Commission", f"${sum(r.get('commission', 0) or 0 for r in funded):,.0f}")
    st.divider()
    if not refs:
        st.info("No referrals yet.")
    for r in refs:
        st.markdown(f"**{r['lead_name']}** | {r['status']} | ${r.get('loan_amount', 0):,.0f}")

# ── ONBOARDING ─────────────────────────────────────────────────────────────────
with tab_onboard:
    st.subheader("Your Onboarding Status")
    completion = db.get_onboarding_completion(realtor['id'])
    st.progress(completion / 100, text=f"{completion:.0f}% complete")
    steps = db.get_onboarding_status(realtor['id'])
    if not steps:
        st.info("No onboarding checklist yet.")
    for step in steps:
        icon = "DONE" if step['completed'] else "PENDING"
        st.markdown(f"**{icon}**: {step['description']}")
