import streamlit as st
import json
import os

CONFIG_FILE = "global_config.json"

# --- Load existing config ---
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {
            "language": ["English", "Tamil", "Hindi", "Japanese"],
            "default_language": "English"
        }

def save_config(updated_config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_config, f, indent=2, ensure_ascii=False)

# --- App UI ---
st.set_page_config(page_title="🌐 Language Preference Editor", layout="centered")
st.title("🌐 Update Global Language Preference")

config = load_config()

# Language selection
available_langs = config.get("language", [])
default_lang = config.get("default_language", "English")

st.markdown("#### Available Languages:")
new_default = st.selectbox("Choose default language", options=available_langs, index=available_langs.index(default_lang))

# Save button
if st.button("💾 Save Default Language"):
    config["default_language"] = new_default
    save_config(config)
    st.success(f"✅ Updated default language to: **{new_default}**")

# Current JSON display
with st.expander("🔍 View Full global_config.json"):
    st.json(config)
