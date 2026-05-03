import streamlit as st
import google.generativeai as genai
import difflib
import language_tool_python

# CONFIG + GLOBAL STYLE
st.set_page_config(page_title="AI Grammar Corrector", layout="centered")

st.markdown("""
<style>
/* Page */
body { background-color: #0e1117; }

/* Cards */
.card {
    padding: 14px;
    border-radius: 12px;
    background: #111827;
    border: 1px solid #1f2937;
}

/* Main result */
.main-result {
    padding: 18px;
    border-radius: 14px;
    background: #0f172a;
    border: 1px solid #1e293b;
    font-size: 18px;
}

/* Input */
textarea {
    border-radius: 12px !important;
}

/* Button */
.stButton button {
    border-radius: 10px;
    height: 48px;
    font-size: 16px;
}
</style>
""", unsafe_allow_html=True)

# HEADER
st.markdown("""
<h1 style='text-align:center;'> AI Grammar Corrector</h1>
<p style='text-align:center;color:gray;'>Fix grammar with AI + explanation</p>
""", unsafe_allow_html=True)

st.divider()

# HELPER FUNCTIONS
def normalize_text(text):
    return text.lower().replace(".", "").strip()

def highlight_changes(original, corrected):
    orig_words = normalize_text(original).split()
    corr_words = normalize_text(corrected).split()

    diff = difflib.SequenceMatcher(None, orig_words, corr_words)
    result = []

    for tag, i1, i2, j1, j2 in diff.get_opcodes():
        if tag == 'equal':
            result.extend(orig_words[i1:i2])
        elif tag == 'replace':
            result.append(f"<span style='color:red;text-decoration:line-through'>{' '.join(orig_words[i1:i2])}</span>")
            result.append(f"<span style='color:lightgreen;font-weight:bold'>{' '.join(corr_words[j1:j2])}</span>")
        elif tag == 'delete':
            result.append(f"<span style='color:red;text-decoration:line-through'>{' '.join(orig_words[i1:i2])}</span>")
        elif tag == 'insert':
            result.append(f"<span style='color:lightgreen;font-weight:bold'>{' '.join(corr_words[j1:j2])}</span>")

    return " ".join(result).capitalize()

def generate_explanation(user_input, corrected):
    explanations = []

    orig_words = normalize_text(user_input).split()
    corr_words = normalize_text(corrected).split()

    diff = difflib.SequenceMatcher(None, orig_words, corr_words)

    number_words = ["two", "three", "four", "five", "six", "seven"]

    for tag, i1, i2, j1, j2 in diff.get_opcodes():
        if tag == "replace":
            o = " ".join(orig_words[i1:i2])
            c = " ".join(corr_words[j1:j2])

            if i1 > 0 and orig_words[i1-1] in number_words:
                explanations.append(f'"{o}" → "{c}" (plural needed after number)')
            elif "yesterday" in user_input.lower():
                explanations.append(f'"{o}" → "{c}" (past tense needed)')
            else:
                explanations.append(f'"{o}" → "{c}" (grammar improvement)')

    if not explanations:
        explanations.append("Sentence is already good.")

    return explanations

# LOAD TOOLS
@st.cache_resource
def load_tools():
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    gemini = genai.GenerativeModel("gemini-1.5-flash")
    tool = language_tool_python.LanguageTool('en-US')
    return gemini, tool

gemini_model, tool = load_tools()

# AI CORRECTION
def ai_correct(text):
    response = gemini_model.generate_content(
        f"Correct the grammar of this sentence. Reply with ONLY the corrected sentence, no explanation, no quotes:\n\n{text}"
    )
    return response.text.strip()

# INPUT
st.markdown("### ✏️ Enter your sentence")

user_input = st.text_area(
    "",
    placeholder="Type your sentence here...",
    height=120
)

if st.button("✨ Check", use_container_width=True):

    if user_input:
        with st.spinner("🔄 Processing..."):

            # Rule-based
            matches = tool.check(user_input)
            rule_corrected = language_tool_python.utils.correct(user_input, matches)

            # ✅ PERUBAHAN 3: Pakai fungsi ai_correct() bukan model T5
            corrected = ai_correct(user_input)

        st.divider()

        # RESULT
        st.markdown("## 📊 Result")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### ❌ Original")
            st.markdown(f"<div class='card'>{user_input}</div>", unsafe_allow_html=True)

        with col2:
            st.markdown("### 🛠 Rule Fix")
            st.markdown(f"<div class='card'>{rule_corrected}</div>", unsafe_allow_html=True)

        # FINAL AI RESULT
        st.markdown("## 🤖 Final AI Correction")
        st.markdown(
            f"<div class='main-result'>{corrected}</div>",
            unsafe_allow_html=True
        )

        # HIGHLIGHT
        st.markdown("## ✨ Changes")
        st.markdown(
            f"<div class='card'>{highlight_changes(user_input, corrected)}</div>",
            unsafe_allow_html=True
        )

        # EXPLANATION
        st.markdown("## 🧠 Explanation")

        explanations = generate_explanation(user_input, corrected)

        for exp in explanations:
            st.markdown(f"💡 {exp}")
