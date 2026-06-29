"""Mobile-optimized Streamlit app for realtors."""
import streamlit as st
from data_manager import DataManager
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Realtor Hub", page_icon="📱", layout="centered",
                   initial_sidebar_state="collapsed")

# Mobile CSS
st.markdown("""
<style>
    .main .block-container { max-width: 420px; padding: 1rem; }
    .stButton > button { width: 100%; font-size: 1.1rem; padding: 0.75rem; }
    h1 { font-size: 1.5rem; }
</style>
""", unsafe_allow_html=True)

db = DataManager()
st.title("📱 Realtor Hub")
st.caption("Mobile App · NEXA Lending")

realtors = db.get_all_realtors()
if not realtors:
    st.warning("No realtors configured.")
    st.stop()

realtor_names = [r['name'] for r in realtors]
selected_name = st.selectbox("Your Name", realtor_names)
realtor = next(r for r in realtors if r['name'] == selected_name)

tab_content, tab_refs = st.tabs(["📄 Content", "🎯 Referrals"])

with tab_content:
    drafts = db.get_content(realtor_id=realtor['id'], status='draft')
    st.markdown(f"**{len(drafts)} items awaiting approval**")
    for d in drafts:
        with st.expander(d['title']):
            st.write(d['body'][:200] + "...")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅", key=f"a_{d['id']}"):
                    db.update_content_status(d['id'], 'approved')
                    st.rerun()
            with col2:
                if st.button("❌", key=f"r_{d['id']}"):
                    db.update_content_status(d['id'], 'rejected')
                    st.rerun()

with tab_refs:
    refs = db.get_referrals(realtor_id=realtor['id'], days=30)
    st.markdown(f"**{len(refs)} referrals in the last 30 days**")
    for r in refs:
        emoji = {'new':'🆕','contacted':'📞','funded':'💰','lost':'❌'}.get(r['status'],'📋')
        st.markdown(f"{emoji} {r['lead_name']} · {r['status']}")
