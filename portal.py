"""Realtor Portal — realtors log in here to approve content and view referrals."""
import streamlit as st
from data_manager import DataManager

st.set_page_config(page_title="Realtor Portal", page_icon="🏡", layout="wide")
db = DataManager()

st.title("🏡 Realtor Content Portal")
st.caption("Powered by NEXA Lending · Kenny Merdan")

realtors = db.get_all_realtors()
if not realtors:
    st.warning("No realtors in the system yet.")
    st.stop()

realtor_names = [f"{r['name']} — {r.get('location','N/A')}" for r in realtors]
selected = st.selectbox("Select your profile", realtor_names)
realtor = realtors[realtor_names.index(selected)]

tab_content, tab_referrals, tab_onboarding = st.tabs(["📄 Content Approval", "🎯 My Referrals", "🚀 Onboarding"])

with tab_content:
    st.subheader("📄 Pending Content Approval")
    drafts = db.get_content(realtor_id=realtor['id'], status='draft')
    if not drafts:
        st.info("No content waiting for approval.")
    for d in drafts:
        with st.expander(f"📄 {d['title']} · {d['created_at'][:10]}"):
            st.markdown(d['body'])
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Approve", key=f"app_{d['id']}", type="primary"):
                    db.update_content_status(d['id'], 'approved')
                    st.success("Approved for publishing!")
                    st.rerun()
            with col2:
                if st.button("❌ Reject", key=f"rej_{d['id']}"):
                    db.update_content_status(d['id'], 'rejected')
                    st.warning("Rejected.")
                    st.rerun()

with tab_referrals:
    st.subheader("🎯 Your Referrals")
    refs = db.get_referrals(realtor_id=realtor['id'], days=90)
    funded = [r for r in refs if r['status'] == 'funded']
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Referrals (90d)", len(refs))
    col2.metric("Funded", len(funded))
    col3.metric("Commission", f"${sum(r.get('commission',0) or 0 for r in funded):,.0f}")
    st.divider()
    for r in refs:
        emoji = {'new':'🆕','contacted':'📞','application':'📝','approved':'✅','funded':'💰','lost':'❌'}.get(r['status'],'📋')
        st.markdown(f"{emoji} **{r['lead_name']}** · {r['status']} · ${r.get('loan_amount',0):,.0f}")

with tab_onboarding:
    st.subheader("🚀 Your Onboarding Status")
    completion = db.get_onboarding_completion(realtor['id'])
    st.progress(completion / 100, text=f"{completion:.0f}% complete")
    steps = db.get_onboarding_status(realtor['id'])
    for step in steps:
        icon = "✅" if step['completed'] else "⏳"
        st.markdown(f"{icon} {step['description']}")
