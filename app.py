import streamlit as st
import requests
import hashlib
import json
import re
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

JWT_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySW5mb3JtYXRpb24iOnsiaWQiOiIxMjVlOThlNS1mOTQ3LTRkZTItOGViZi0zYzUwMzA3OGUwNTgiLCJlbWFpbCI6ImFic3RyYWN0YXJ0Njk0MjA4OEBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwicGluX3BvbGljeSI6eyJyZWdpb25zIjpbeyJkZXNpcmVkUmVwbGljYXRpb25Db3VudCI6MSwiaWQiOiJGUkExIn0seyJkZXNpcmVkUmVwbGljYXRpb25Db3VudCI6MSwiaWQiOiJOWUMxIn1dLCJ2ZXJzaW9uIjoxfSwibWZhX2VuYWJsZWQiOmZhbHNlLCJzdGF0dXMiOiJBQ1RJVkUifSwiYXV0aGVudGljYXRpb25UeXBlIjoic2NvcGVkS2V5Iiwic2NvcGVkS2V5S2V5IjoiMGMzY2ZmYWRlMzlmNDIzMzhkZjQiLCJzY29wZWRLZXlTZWNyZXQiOiI4YzM2ZWU0MmMzMjEyZTJiMGJkODUyNWNhZjY2OWFhZDEwNmM4MmMxODNjMTE0MjA1ZWE5ZDRmYzEyNmExNzc5IiwiZXhwIjoxODA2NjU1Nzc0fQ.qf6iXOMJhg2Gas_1adtdTqtxEWt4MTv3tpx-c_ad7Wg"


PII_MASK_MAP = {
    "PERSON": "[NAME]",
    "EMAIL_ADDRESS": "[EMAIL]",
    "PHONE_NUMBER": "[PHONE_NUMBER]",
    "CREDIT_CARD": "[CREDIT_CARD_NUMBER]",
    "US_BANK_ACCOUNT": "[BANK_ACCOUNT]",
    "iban": "[IBAN]",
    "ADDRESS": "[ADDRESS]",
    "US_SSN": "[SSN]",
    "SSN": "[SSN]",
    "NRP": "[GOVERNMENT_ID]",
    "EMPLOYEE_ID": "[EMPLOYEE_ID]",
    "PAN_CARD": "[PAN_CARD]",
    "INDIAN_PAN": "[PAN_CARD]",
    "ACCOUNT_NUMBER": "[ACCOUNT_NUMBER]",
    "BANK_ACCOUNT": "[ACCOUNT_NUMBER]",
}


def hash_value(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:16]


def upload_to_ipfs(data, filename="data.json"):
    url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
    files = {"file": (filename, data)}
    headers = {"Authorization": f"Bearer {JWT_KEY}"}
    response = requests.post(url, files=files, headers=headers)
    return response.json()


def detect_pan(text):
    pan_patterns = [
        r"[A-Z]{5}[0-9]{4}[A-Z]",
        r"PAN\s*[:\-]?\s*[A-Z]{5}[0-9]{4}[A-Z]",
    ]
    results = []
    for pattern in pan_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            results.append(
                {
                    "entity_type": "INDIAN_PAN",
                    "start": match.start(),
                    "end": match.end(),
                    "score": 0.95,
                    "text": match.group(),
                }
            )
    return results


def detect_account(text):
    patterns = [
        r"\b[0-9]{9,18}\b",
        r"account\s*[:\-]?\s*[0-9]{9,18}",
        r"a/c\s*[:\-]?\s*[0-9]{9,18}",
    ]
    results = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            val = match.group()
            if "account" in val.lower() or "a/c" in val.lower():
                val = re.sub(r"^[a/ca/c\s:]+", "", val, flags=re.IGNORECASE).strip()
            if val.isdigit():
                results.append(
                    {
                        "entity_type": "ACCOUNT_NUMBER",
                        "start": match.start(),
                        "end": match.end(),
                        "score": 0.9,
                        "text": val,
                    }
                )
    return results


st.set_page_config(page_title="Hyper-ABS", page_icon="🛡️", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Oxanium:wght@400;600;700&display=swap');
    
    :root {
        --background: oklch(0.2161 0.0061 56.0434);
        --foreground: oklch(0.9699 0.0013 106.4238);
        --card: oklch(0.2685 0.0063 34.2976);
        --card-foreground: oklch(0.9699 0.0013 106.4238);
        --primary: oklch(0.7049 0.1867 47.6044);
        --primary-foreground: oklch(1.0000 0 0);
        --secondary: oklch(0.4444 0.0096 73.6390);
        --secondary-foreground: oklch(0.9232 0.0026 48.7171);
        --muted: oklch(0.2330 0.0073 67.4563);
        --muted-foreground: oklch(0.7161 0.0091 56.2590);
        --accent: oklch(0.3598 0.0497 229.3202);
        --accent-foreground: oklch(0.9232 0.0026 48.7171);
        --destructive: oklch(0.5771 0.2152 27.3250);
        --destructive-foreground: oklch(1.0000 0 0);
        --border: oklch(0.3741 0.0087 67.5582);
        --radius: 0.3rem;
    }
    
    * {
        font-family: 'Oxanium', sans-serif;
    }
    
    .stApp {
        background-color: var(--background);
    }
    
    .title {
        font-size: 3rem;
        font-weight: 700;
        color: var(--primary);
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        font-size: 1.1rem;
        color: var(--muted-foreground);
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .card {
        background-color: var(--card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1.5rem;
        box-shadow: 0px 2px 3px 0px hsl(0 0% 5% / 0.45);
    }
    
    .card-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--card-foreground);
        margin-bottom: 1rem;
    }
    
    .success-box {
        padding: 1rem;
        background-color: oklch(0.2685 0.0063 34.2976);
        border: 1px solid var(--primary);
        border-radius: var(--radius);
        margin-top: 1rem;
    }
    
    .success-box code {
        color: var(--primary);
        word-break: break-all;
    }
    
    .entity-tag {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        background-color: var(--accent);
        border-radius: 9999px;
        font-size: 0.875rem;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
        color: var(--accent-foreground);
    }
    
    .stTextArea textarea {
        background-color: var(--card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        color: var(--foreground);
    }
    
    .stTextArea textarea:focus {
        border-color: var(--primary);
        box-shadow: 0 0 0 2px var(--primary);
    }
    
    div[data-testid="stTextArea"] label {
        color: var(--foreground);
        font-weight: 600;
    }
    
    .stMarkdown, .stSubheader {
        color: var(--foreground);
    }
    
    section[data-testid="stSidebar"] {
        background-color: var(--card);
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.markdown('<div class="title">🛡️ Hyper-ABS</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Automatic PII Detection & Secure IPFS Storage</div>',
    unsafe_allow_html=True,
)

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">📝 Input Text</div>', unsafe_allow_html=True)
    input_text = st.text_area(
        "Enter text containing PII:",
        height=280,
        placeholder="e.g., My PAN is AABCV1234D and account 998877665544...",
    )
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="card-title">🔒 Anonymized Output</div>', unsafe_allow_html=True
    )

    if input_text:
        analyzer = AnalyzerEngine()
        analyzer_results = analyzer.analyze(text=input_text, language="en")

        pan_results = detect_pan(input_text)
        account_results = detect_account(input_text)

        class SimpleResult:
            def __init__(self, entity_type, start, end, score, text):
                self.entity_type = entity_type
                self.start = start
                self.end = end
                self.score = score
                self.text = text

            def __repr__(self):
                return f"SimpleResult(entity_type={self.entity_type}, start={self.start}, end={self.end})"

        custom_results = []
        for r in pan_results:
            custom_results.append(
                SimpleResult(
                    r["entity_type"], r["start"], r["end"], r["score"], r["text"]
                )
            )
        for r in account_results:
            custom_results.append(
                SimpleResult(
                    r["entity_type"], r["start"], r["end"], r["score"], r["text"]
                )
            )

        all_results = list(analyzer_results) + custom_results

        sorted_results = sorted(all_results, key=lambda x: x.start)

        pii_data = {}
        masked_text = input_text
        all_entities = [r.entity_type for r in sorted_results]

        operator_config = {}
        for entity_type, mask_text in PII_MASK_MAP.items():
            if entity_type in all_entities:
                operator_config[entity_type] = OperatorConfig(
                    "replace", {"new_value": mask_text}
                )

        if operator_config:
            anonymizer = AnonymizerEngine()
            anonymized_results = anonymizer.anonymize(
                text=input_text,
                analyzer_results=list(sorted_results),
                operators=operator_config,
            )
            masked_text = anonymized_results.text
        else:
            masked_text = input_text

        for result in sorted_results:
            pii_value = input_text[result.start : result.end]
            key = f"{result.entity_type}_{result.start}"
            entity_label = result.entity_type
            if result.entity_type == "US_SSN" or result.entity_type == "SSN":
                entity_label = "SSN"
            elif result.entity_type == "PERSON":
                entity_label = "NAME"
            elif result.entity_type == "INDIAN_PAN":
                entity_label = "PAN_CARD"
            pii_data[key] = {
                "original": pii_value,
                "hashed": hash_value(pii_value),
                "entity_type": entity_label,
                "position": f"{result.start}-{result.end}",
                "score": round(result.score, 2),
            }

        st.text_area(
            "Anonymized Text:",
            value=masked_text,
            height=80,
            disabled=True,
            label_visibility="collapsed",
        )

        ipfs_result = upload_to_ipfs(json.dumps(pii_data, indent=2))
        if "IpfsHash" in ipfs_result:
            st.markdown(
                f"""
                <div class="success-box">
                    <strong>✅ Auto-uploaded to IPFS</strong><br>
                    <code>ipfs://{ipfs_result["IpfsHash"]}</code>
                </div>
            """,
                unsafe_allow_html=True,
            )
        else:
            st.error(f"Error uploading: {ipfs_result}")

        st.markdown(
            '<div class="card-title" style="margin-top: 1rem;">📊 Detected Entities</div>',
            unsafe_allow_html=True,
        )
        if sorted_results:
            for result in sorted_results:
                st.markdown(
                    f'<span class="entity-tag">{result.entity_type}</span> '
                    f"Pos: {result.start}-{result.end} | Score: {result.score:.2f}",
                    unsafe_allow_html=True,
                )
        else:
            st.info("No PII detected")

    st.markdown("</div>", unsafe_allow_html=True)
