"""Realtor Portal - guided wizard to create and publish content."""
import streamlit as st
from data_manager import DataManager


PLATFORMS = {
    "Facebook": {"icon": "f", "color": "#1877F2", "char_limit": 63206},
    "Instagram": {"icon": "ig", "color": "#E4405F", "char_limit": 2200},
    "LinkedIn": {"icon": "in", "color": "#0A66C2", "char_limit": 3000},
    "Google Business": {"icon": "g", "color": "#34A853", "char_limit": 1500},
    "Blog / WordPress": {"icon": "wp", "color": "#21759B", "char_limit": 99999},
}


def fallback_content(name, location, platform, topic, tone):
    tag = location.replace(" ", "").replace(",", "")
    if platform in ("Facebook", "Instagram", "LinkedIn"):
        if platform == "Instagram":
            lines = [
                topic + " - here is what every buyer and seller in " + location + " needs to know.",
                "",
                "The market moves fast. Are you ready?",
                "",
                "DM me for a free consultation. Link in bio.",
                "",
                "#RealEstate #" + tag + " #HomeBuying #HomeSelling #Realtor #" + location.split(",")[0].replace(" ", ""),
            ]
        elif platform == "LinkedIn":
            lines = [
                "Real estate insight for " + location + ":",
                "",
                topic,
                "",
                "Here is what I am seeing in the market right now:",
                "- Buyers who are pre-approved are winning deals",
                "- Sellers who price right are closing fast",
                "- Local expertise is more valuable than ever",
                "",
                "If you or someone you know is thinking about buying or selling, let's connect.",
                "",
                "#RealEstate #" + tag + " #Realtor",
            ]
        else:
            lines = [
                "Thinking about buying or selling in " + location + "?",
                "",
                topic,
                "",
                "As your local real estate expert, I am here to guide you every step of the way.",
                "",
                "Message me or call today - let's talk about your goals.",
                "",
                "#RealEstate #" + tag + " #HomeBuying #HomeSelling",
            ]
        return "\n".join(lines)
    elif platform == "Google Business":
        lines = [
            topic,
            "",
            name + " is your trusted real estate expert in " + location + ".",
            "Whether you are buying, selling, or investing - local knowledge makes all the difference.",
            "",
            "Call today for a free consultation!",
        ]
        return "\n".join(lines)
    else:
        lines = [
            "# " + topic,
            "",
            "*By " + name + " | " + location + "*",
            "",
            "## Introduction",
            "",
            "If you have been wondering about " + topic.lower() + ", you are not alone.",
            "As a real estate professional serving " + location + ", I get this question all the time.",
            "",
            "## What You Need to Know",
            "",
            "The " + location + " market is constantly evolving. Here are the key things to keep in mind:",
            "",
            "**1. Timing matters.** The right move at the right time can save or earn you thousands.",
            "**2. Local knowledge is priceless.** A local agent knows the neighborhoods, the trends, and the opportunities.",
            "**3. Preparation beats hesitation.** Whether buying or selling, getting prepared early puts you ahead.",
            "",
            "## Ready to Take the Next Step?",
            "",
            "Reach out today and let's put a plan together for your real estate goals.",
            "",
            "---",
            "*" + name + " | Real Estate Professional | " + location + "*",
        ]
        return "\n".join(lines)


def try_ai_generate(realtor, platform, topic, tone):
    try:
        from ai_suggestions.ai_suggester import AISuggester
        suggester = AISuggester()
        return suggester.generate_content(
            realtor=realtor,
            content_type=platform,
            topic=topic,
            tone=tone
        )
    except Exception:
        return fallback_content(
            realtor.get("name", ""),
            realtor.get("location", "your area"),
            platform,
            topic,
            tone
        )


def try_publish_facebook(content, realtor):
    try:
        import requests
        import streamlit as st
        token = st.secrets.get("FACEBOOK_PAGE_ACCESS_TOKEN", "")
        page_id = realtor.get("facebook_page_id", "")
        if not token or not page_id:
            return False, "Facebook not connected. Add FACEBOOK_PAGE_ACCESS_TOKEN and your Page ID to Streamlit Secrets."
        resp = requests.post(
            "https://graph.facebook.com/v19.0/" + page_id + "/feed",
            data={"message": content, "access_token": token},
            timeout=10
        )
        data = resp.json()
        if "id" in data:
            return True, "Posted to Facebook! Post ID: " + data["id"]
        return False, "Facebook error: " + str(data.get("error", {}).get("message", resp.text))
    except Exception as e:
        return False, "Facebook publish failed: " + str(e)


def try_publish_instagram(content, realtor):
    return False, "Instagram direct posting requires a media URL. Copy your caption below and paste it when creating your Instagram post."


def try_publish_gmb(content, realtor):
    try:
        import requests
        import streamlit as st
        token = st.secrets.get("GOOGLE_ACCESS_TOKEN", "")
        location_id = realtor.get("google_business_id", "")
        if not token or not location_id:
            return False, "Google Business not connected. Add GOOGLE_ACCESS_TOKEN and your Location ID to Streamlit Secrets."
        resp = requests.post(
            "https://mybusiness.googleapis.com/v4/" + location_id + "/localPosts",
            headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
            json={"languageCode": "en-US", "summary": content, "topicType": "STANDARD"},
            timeout=10
        )
        if resp.status_code == 200:
            return True, "Posted to Google Business Profile!"
        return False, "Google Business error: " + resp.text
    except Exception as e:
        return False, "Google Business publish failed: " + str(e)


def try_publish_wordpress(content, topic, realtor):
    try:
        import requests
        import base64
        import streamlit as st
        site_url = st.secrets.get("WORDPRESS_SITE_URL", "") or realtor.get("website", "")
        username = st.secrets.get("WORDPRESS_USERNAME", "")
        app_password = st.secrets.get("WORDPRESS_APP_PASSWORD", "")
        if not site_url or not username or not app_password:
            return False, "WordPress not connected. Add WORDPRESS_SITE_URL, WORDPRESS_USERNAME, and WORDPRESS_APP_PASSWORD to Streamlit Secrets."
        site_url = site_url.rstrip("/")
        creds = base64.b64encode((username + ":" + app_password).encode()).decode()
        resp = requests.post(
            site_url + "/wp-json/wp/v2/posts",
            headers={"Authorization": "Basic " + creds, "Content-Type": "application/json"},
            json={"title": topic, "content": content, "status": "publish"},
            timeout=15
        )
        data = resp.json()
        if resp.status_code in (200, 201) and "id" in data:
            return True, "Published to WordPress! View at: " + data.get("link", site_url)
        return False, "WordPress error: " + str(data.get("message", resp.text))
    except Exception as e:
        return False, "WordPress publish failed: " + str(e)


def try_publish_linkedin(content, realtor):
    return False, "LinkedIn API requires OAuth2 setup. Copy your post below and paste it on LinkedIn."


def step_profile(db):
    st.markdown("## Step 1 of 3 - Your Profile")
    st.caption("Tell us about yourself. You only need to do this once.")

    realtors = db.get_all_realtors()
    realtor_names = [r["name"] + " (" + r.get("location", "N/A") + ")" for r in realtors]

    col_a, col_b = st.columns([2, 1])
    with col_a:
        if realtors:
            option = st.radio(
                "Are you already in the system?",
                ["I am already set up - select my profile", "I am new - create my profile"],
                horizontal=True
            )
        else:
            option = "I am new - create my profile"
            st.info("No profiles yet. Fill in your info below to get started.")

    if realtors and "already set up" in option:
        selected = st.selectbox("Select your name", realtor_names)
        realtor = realtors[realtor_names.index(selected)]
        st.success("Welcome back, " + realtor["name"] + "!")

        with st.expander("Update your social accounts"):
            col1, col2 = st.columns(2)
            with col1:
                fb = st.text_input("Facebook Page ID", value=realtor.get("facebook_page_id", ""))
                ig = st.text_input("Instagram Handle", value=realtor.get("instagram_handle", ""))
                li = st.text_input("LinkedIn Profile URL", value=realtor.get("linkedin_url", ""))
            with col2:
                gmb = st.text_input("Google Business Location ID", value=realtor.get("google_business_id", ""))
                wp = st.text_input("WordPress Site URL", value=realtor.get("website", ""))
            if st.button("Save Updates"):
                db.update_realtor(realtor["id"], {
                    "facebook_page_id": fb,
                    "instagram_handle": ig,
                    "google_business_id": gmb,
                    "website": wp,
                })
                st.success("Profile updated!")

        if st.button("Continue to Create Content", type="primary", use_container_width=True):
            st.session_state["portal_realtor"] = realtor
            st.session_state["wizard_step"] = 1
            st.rerun()
    else:
        with st.form("new_profile"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Your Full Name *")
                email = st.text_input("Email")
                phone = st.text_input("Phone")
                location = st.text_input("City, State (e.g. Scottsdale, AZ) *")
            with col2:
                fb = st.text_input("Facebook Page ID", help="Found in your Facebook Page settings under 'About'")
                ig = st.text_input("Instagram Handle", help="Your @username without the @")
                gmb = st.text_input("Google Business Location ID", help="From your Google Business Profile dashboard")
                wp = st.text_input("Your Website / Blog URL", help="e.g. https://yoursite.com")
            submitted = st.form_submit_button("Create My Profile & Continue", type="primary", use_container_width=True)
            if submitted:
                if not name or not location:
                    st.error("Name and location are required.")
                else:
                    rid = db.add_realtor(
                        name, email, phone, location,
                        website=wp,
                        google_business_id=gmb,
                        facebook_page_id=fb,
                        instagram_handle=ig,
                    )
                    db.create_onboarding_checklist(rid)
                    realtor = {"id": rid, "name": name, "email": email, "phone": phone,
                               "location": location, "website": wp, "google_business_id": gmb,
                               "facebook_page_id": fb, "instagram_handle": ig}
                    st.session_state["portal_realtor"] = realtor
                    st.session_state["wizard_step"] = 1
                    st.rerun()


def step_create(db):
    realtor = st.session_state.get("portal_realtor", {})
    st.markdown("## Step 2 of 3 - Create Your Content")
    st.caption("Pick a platform, describe your topic, and we will write it for you.")

    st.markdown("### Where do you want to post?")
    cols = st.columns(len(PLATFORMS))
    platform_keys = list(PLATFORMS.keys())
    selected_platform = st.session_state.get("selected_platform", platform_keys[0])

    for i, (col, key) in enumerate(zip(cols, platform_keys)):
        p = PLATFORMS[key]
        is_selected = (key == selected_platform)
        border = "3px solid " + p["color"] if is_selected else "1px solid #ddd"
        bg = p["color"] + "11" if is_selected else "white"
        col.markdown(
            '<div style="border:' + border + ';border-radius:12px;padding:12px;text-align:center;background:' + bg + ';cursor:pointer;">'
            '<div style="font-size:1.5rem;font-weight:bold;color:' + p["color"] + ';">' + p["icon"].upper() + '</div>'
            '<div style="font-weight:' + ("bold" if is_selected else "normal") + ';font-size:0.85rem;">' + key + '</div>'
            '</div>',
            unsafe_allow_html=True
        )
        if col.button("Select", key="plat_" + key, use_container_width=True):
            st.session_state["selected_platform"] = key
            st.rerun()

    st.divider()

    col_form, col_preview = st.columns([1, 1])
    with col_form:
        topic = st.text_area(
            "What do you want to post about?",
            placeholder="e.g. Why now is a great time to buy in " + realtor.get("location", "your area") + "\ne.g. 5 tips for first-time homebuyers\ne.g. Just listed: 3 bed 2 bath in [neighborhood]",
            height=120,
            value=st.session_state.get("portal_topic", "")
        )
        tone = st.select_slider(
            "Tone",
            options=["Casual", "Friendly", "Professional", "Expert"],
            value=st.session_state.get("portal_tone", "Friendly")
        )
        char_limit = PLATFORMS[selected_platform]["char_limit"]
        if char_limit < 99999:
            st.caption("Platform character limit: " + str(char_limit))

        col_gen, col_back = st.columns([2, 1])
        with col_gen:
            generate = st.button("Write My Content", type="primary", use_container_width=True)
        with col_back:
            if st.button("Back", use_container_width=True):
                st.session_state["wizard_step"] = 0
                st.rerun()

        if generate:
            if not topic.strip():
                st.warning("Please describe what you want to post about.")
            else:
                with st.spinner("Writing your " + selected_platform + " content..."):
                    content = try_ai_generate(realtor, selected_platform, topic, tone)
                    st.session_state["generated_content"] = content
                    st.session_state["portal_topic"] = topic
                    st.session_state["portal_tone"] = tone
                    st.session_state["selected_platform"] = selected_platform

    with col_preview:
        st.markdown("**Preview**")
        content = st.session_state.get("generated_content", "")
        if content:
            char_count = len(content)
            char_limit = PLATFORMS[selected_platform]["char_limit"]
            if char_count > char_limit:
                st.warning("Content is " + str(char_count) + " characters. Limit for " + selected_platform + " is " + str(char_limit) + ". Consider shortening.")
            else:
                st.caption(str(char_count) + " / " + (str(char_limit) if char_limit < 99999 else "unlimited") + " characters")
            st.text_area("Edit before publishing", content, height=280, key="editable_content")
            col_copy, col_next = st.columns(2)
            with col_copy:
                st.download_button(
                    "Download .txt",
                    data=st.session_state.get("editable_content", content),
                    file_name=selected_platform.replace(" ", "_") + "_post.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            with col_next:
                if st.button("Publish This Post", type="primary", use_container_width=True):
                    db.save_content(
                        realtor["id"],
                        selected_platform,
                        topic,
                        st.session_state.get("editable_content", content)
                    )
                    st.session_state["wizard_step"] = 2
                    st.rerun()
        else:
            st.info("Your content will appear here. Fill in the topic and click Write My Content.")


def step_publish(db):
    realtor = st.session_state.get("portal_realtor", {})
    platform = st.session_state.get("selected_platform", "Facebook")
    content = st.session_state.get("editable_content") or st.session_state.get("generated_content", "")
    topic = st.session_state.get("portal_topic", "Post")

    st.markdown("## Step 3 of 3 - Review & Publish")
    st.caption("Your content is ready. Publish directly or copy and post manually.")

    col_content, col_actions = st.columns([3, 2])

    with col_content:
        p = PLATFORMS.get(platform, {})
        color = p.get("color", "#555")
        st.markdown(
            '<div style="border-left:4px solid ' + color + ';padding:16px;background:#fafafa;border-radius:8px;">'
            '<div style="font-size:0.75rem;color:' + color + ';font-weight:bold;margin-bottom:8px;">' + platform.upper() + '</div>'
            + content.replace("\n", "<br>") +
            '</div>',
            unsafe_allow_html=True
        )

    with col_actions:
        st.markdown("**Publishing Options**")

        if platform == "Facebook":
            fb_id = realtor.get("facebook_page_id", "")
            if fb_id:
                if st.button("Post to Facebook Page", type="primary", use_container_width=True):
                    ok, msg = try_publish_facebook(content, realtor)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
            else:
                st.info("Add your Facebook Page ID in your profile to enable direct posting.")

        elif platform == "Instagram":
            st.info("Instagram requires posting through the app. Copy your caption below.")

        elif platform == "LinkedIn":
            st.info("LinkedIn requires OAuth setup. Copy your post and paste it on LinkedIn.")

        elif platform == "Google Business":
            gmb_id = realtor.get("google_business_id", "")
            if gmb_id:
                if st.button("Post to Google Business", type="primary", use_container_width=True):
                    ok, msg = try_publish_gmb(content, realtor)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
            else:
                st.info("Add your Google Business Location ID in your profile to enable direct posting.")

        elif platform == "Blog / WordPress":
            wp_url = realtor.get("website", "")
            if wp_url:
                if st.button("Publish to WordPress", type="primary", use_container_width=True):
                    ok, msg = try_publish_wordpress(content, topic, realtor)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
            else:
                st.info("Add your WordPress site URL in your profile to enable direct publishing.")

        st.divider()

        platform_links = {
            "Facebook": "https://www.facebook.com/",
            "Instagram": "https://www.instagram.com/",
            "LinkedIn": "https://www.linkedin.com/feed/",
            "Google Business": "https://business.google.com/",
            "Blog / WordPress": realtor.get("website", "https://wordpress.com/"),
        }
        st.markdown("**Or post manually:**")
        st.markdown("1. Copy your content above")
        st.markdown("2. [Open " + platform + "](" + platform_links.get(platform, "#") + ")")
        st.markdown("3. Create a new post and paste")

        st.divider()
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Create Another Post", use_container_width=True):
                st.session_state["generated_content"] = ""
                st.session_state["portal_topic"] = ""
                st.session_state["wizard_step"] = 1
                st.rerun()
        with col_b:
            if st.button("View My Drafts", use_container_width=True):
                st.session_state["show_drafts"] = True
                st.session_state["wizard_step"] = 3
                st.rerun()


def step_drafts(db):
    realtor = st.session_state.get("portal_realtor", {})
    if not realtor:
        st.warning("No profile loaded.")
        return

    st.markdown("## Your Content History")
    drafts = db.get_content(realtor_id=realtor["id"])
    if not drafts:
        st.info("No posts yet. Go back and create your first one!")
    else:
        for d in drafts:
            status_color = {"draft": "#999", "approved": "#34A853", "published": "#1877F2"}.get(d["status"], "#999")
            with st.expander(d["content_type"] + " - " + d["title"][:60] + " (" + d["created_at"][:10] + ")"):
                st.markdown(d["body"])
                st.caption(
                    '<span style="color:' + status_color + ';font-weight:bold;">' + d["status"].upper() + '</span>',
                    unsafe_allow_html=True
                )

    if st.button("Back to Create Content", type="primary"):
        st.session_state["show_drafts"] = False
        st.session_state["wizard_step"] = 1
        st.rerun()


def render():
    db = DataManager()

    if "wizard_step" not in st.session_state:
        st.session_state["wizard_step"] = 0
    if "selected_platform" not in st.session_state:
        st.session_state["selected_platform"] = "Facebook"

    step = st.session_state["wizard_step"]

    st.markdown("""
<style>
.step-indicator { display:flex; gap:8px; margin-bottom:8px; }
.step-dot { width:28px; height:28px; border-radius:50%; display:flex; align-items:center;
            justify-content:center; font-size:0.75rem; font-weight:bold; }
</style>
""", unsafe_allow_html=True)

    if step < 3:
        step_labels = ["Profile", "Create", "Publish"]
        dots = ""
        for i, label in enumerate(step_labels):
            if i < step:
                dots += '<div class="step-dot" style="background:#34A853;color:white;">&#10003;</div>'
            elif i == step:
                dots += '<div class="step-dot" style="background:#1877F2;color:white;">' + str(i+1) + '</div>'
            else:
                dots += '<div class="step-dot" style="background:#eee;color:#999;">' + str(i+1) + '</div>'
            if i < len(step_labels) - 1:
                dots += '<div style="flex:1;height:2px;background:' + ("#34A853" if i < step else "#eee") + ';margin:auto;"></div>'
        st.markdown('<div class="step-indicator">' + dots + "</div>", unsafe_allow_html=True)
        st.caption("  ".join([("**" + l + "**" if i == step else l) for i, l in enumerate(step_labels)]))
        st.divider()

    if step == 0:
        step_profile(db)
    elif step == 1:
        step_create(db)
    elif step == 2:
        step_publish(db)
    elif step == 3:
        step_drafts(db)
