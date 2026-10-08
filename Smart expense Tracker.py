import streamlit as st
import pandas as pd
import json
from groq import Groq

st.set_page_config(page_title="Student Expense Tracker", page_icon="💳", layout="centered")

st.title("💳 Smart Student Expense Categorizer")
st.markdown("Paste unstructured daily expenses to automatically classify, tabulate, and visualize your spending.")

with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Enter Groq API Key:", type="password", placeholder="gsk_...")
    st.markdown("[Get a free Groq API key](https://console.groq.com/keys)")

default_input = """Bought college calculus book 45
Bus pass recharge 20
Canteen lunch and coffee 8.5
Netflix subscription 10
Lab notebook and pens 6
Late night pizza with study group 15"""

user_text = st.text_area("Enter your expenses (one per line, with amounts):", default_input, height=150)

if st.button("Categorize & Analyze", type="primary"):
    if not api_key:
        st.error("Please provide a Groq API key in the sidebar.")
    elif not user_text.strip():
        st.warning("Please enter at least one expense line.")
    else:
        try:
            with st.spinner("Classifying expenses with AI..."):
                client = Groq(api_key=api_key)
                
                system_prompt = (
                    "You are a financial parsing assistant. Extract every expense from the provided text into a valid JSON array of objects. "
                    "Each object MUST have these exact keys:\n"
                    "- 'item' (string description)\n"
                    "- 'amount' (float numeric value)\n"
                    "- 'category' (strictly one of: 'Academic', 'Food & Dining', 'Transport', 'Entertainment', 'Personal Care', 'Other')\n\n"
                    "Output ONLY the raw JSON array. Do not include markdown formatting or backticks."
                )

                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    temperature=0.0,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_text}
                    ]
                )
                
                raw_json = response.choices[0].message.content.strip()
                # Clean up if the model outputs markdown blocks
                if raw_json.startswith("```"):
                    raw_json = raw_json.strip("`").replace("json\n", "", 1).strip()

                parsed_data = json.loads(raw_json)
                df = pd.DataFrame(parsed_data)
                
                st.success("Expenses Parsed Successfully!")
                
                # Metrics row
                total_spent = df["amount"].sum()
                col1, col2 = st.columns(2)
                col1.metric("Total Spending", f"${total_spent:.2f}")
                col2.metric("Total Transactions", len(df))
                
                st.subheader("Itemized Breakdown")
                st.dataframe(df, use_container_width=True)
                
                # Category breakdown
                st.subheader("Category Distribution")
                category_summary = df.groupby("category")["amount"].sum()
                st.bar_chart(category_summary)
                
        except json.JSONDecodeError:
            st.error("Model did not return valid JSON. Please try running again.")
        except Exception as e:
            st.error(f"Error parsing data: {str(e)}")
