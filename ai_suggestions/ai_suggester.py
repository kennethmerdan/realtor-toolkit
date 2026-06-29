import os

class AISuggester:
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY") or self._load_from_config()

    def _load_from_config(self):
        try:
            import yaml
            with open("config.yaml") as f:
                cfg = yaml.safe_load(f)
            return cfg.get("openai_api_key")
        except Exception:
            return None

    def generate_content(self, realtor, content_type, topic, tone="Professional"):
        if not self.api_key:
            return self._fallback_content(realtor, content_type, topic, tone)
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            prompt = f"""You are a content writer for {realtor['name']}, a realtor in {realtor.get('location','the local area')}.
Write a {tone.lower()} {content_type.lower()} about: {topic}
Make it engaging, local, and include a call to action. Keep it under 500 words."""
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            return self._fallback_content(realtor, content_type, topic, tone) + f"\n\n*Note: AI error — {e}*"

    def _fallback_content(self, realtor, content_type, topic, tone):
        return f"""# {topic}

*{content_type} for {realtor['name']} · {realtor.get('location','Local Area')}*

Are you thinking about buying or selling in {realtor.get('location','our area')}?
As your trusted local real estate expert, I'm here to help you every step of the way.

{topic} is something many of my clients ask about. Here's what you need to know:

1. The local market is constantly evolving — staying informed is key.
2. Working with an experienced professional saves you time and money.
3. Working with a trusted local expert can save you thousands.

Ready to take the next step? Contact me today!

*— {realtor['name']}*
*Partnered with Kenny Merdan*

---
*To enable AI-powered content, add your OpenAI API key to config.yaml*
"""
