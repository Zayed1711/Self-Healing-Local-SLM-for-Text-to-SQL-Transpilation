import streamlit as st
import sqlite3
import ollama

# --- CONFIGURATION ---
DB_NAME = "inventory_database.db"
MODEL_NAME = "qwen2.5-coder:1.5b"

# --- THE BODY (Database Execution) ---
def test_sql_silently(sql):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        cursor.fetchall()
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def run_sql_query(sql):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        data = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]
        return data, column_names
    except Exception as e:
        return str(e), None
    finally:
        conn.close()

# --- THE BRAIN (Now with Long-Term Memory!) ---
def get_sql_with_self_correction(chat_history, current_query, max_retries=3):
    schema = """
    Table: Customers (customer_id, customer_name, city)
    Table: Products (product_id, product_name, price, stock_quantity)
    """
    
    system_prompt = f"""You are a strict SQLite expert. 
    Rule 1: Return ONLY valid SQL. 
    Rule 2: Do NOT use tables or columns that do not exist in the schema. 
    Rule 3: If the question CANNOT be answered with the provided schema, return exactly the word: UNANSWERABLE.
    Schema:\n{schema}"""
    
    # 1. Start with the system prompt
    conversation_context = [{'role': 'system', 'content': system_prompt}]
    
    # 2. Inject the PAST conversation history so the AI remembers context
    for msg in chat_history:
        # We only feed the AI the raw SQL it generated previously, not our UI text
        if msg["role"] == "user":
            conversation_context.append({'role': 'user', 'content': msg["content"]})
        elif msg["role"] == "assistant" and msg.get("sql"):
            conversation_context.append({'role': 'assistant', 'content': msg["sql"]})
            
    # 3. Add the NEW question
    conversation_context.append({'role': 'user', 'content': current_query})
    
    # The Self-Correction Loop
    for attempt in range(1, max_retries + 1):
        response = ollama.chat(model=MODEL_NAME, messages=conversation_context)
        ai_sql = response['message']['content'].replace("```sql", "").replace("```", "").strip()
        
        if "UNANSWERABLE" in ai_sql.upper():
            return "UNANSWERABLE", attempt
            
        conversation_context.append({'role': 'assistant', 'content': ai_sql})
        is_valid, error_msg = test_sql_silently(ai_sql)
        
        if is_valid:
            return ai_sql, attempt
        else:
            if attempt < max_retries:
                correction_prompt = f"Executing that SQL gave this SQLite error: '{error_msg}'. Fix this error. Remember you ONLY have the Customers and Products tables. If it's impossible, reply with UNANSWERABLE."
                conversation_context.append({'role': 'user', 'content': correction_prompt})
            else:
                return "FAILED", attempt

# --- THE FACE (Streamlit UI) ---
st.set_page_config(page_title="Conversational Data Assistant", layout="wide")
st.title("🧠 Conversational AI Database Assistant")
st.markdown("*Now with Contextual Memory!*")

# --- INITIALIZE MEMORY ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- DRAW PAST MESSAGES ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["display_text"])
        if "sql" in msg and msg["sql"] != "UNANSWERABLE" and msg["sql"] != "FAILED":
             with st.expander("View SQL"):
                 st.code(msg["sql"], language="sql")
             # Re-run the query to show the table for past messages
             results, columns = run_sql_query(msg["sql"])
             if columns:
                 st.dataframe([dict(zip(columns, row)) for row in results], use_container_width=True)

# --- HANDLE NEW INPUT ---
user_input = st.chat_input("Ex: Show me all products...")

if user_input:
    # 1. Add user message to memory and display it
    st.session_state.messages.append({"role": "user", "content": user_input, "display_text": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # 2. Get AI response (passing the past memory!)
    with st.spinner("Analyzing context and generating SQL..."):
        # Pass all messages EXCEPT the one we just added to the get_sql function
        generated_sql, attempts = get_sql_with_self_correction(st.session_state.messages[:-1], user_input)
    
    # 3. Handle the Response & Save to Memory
    with st.chat_message("assistant"):
        if generated_sql == "UNANSWERABLE":
            display_text = "⚠️ **Data Not Available:** I do not have the necessary data to answer that."
            st.warning(display_text)
            st.session_state.messages.append({"role": "assistant", "display_text": display_text, "sql": "UNANSWERABLE"})
            
        elif "FAILED" in generated_sql:
            display_text = "🚨 **System Error:** I couldn't generate a valid query."
            st.error(display_text)
            st.session_state.messages.append({"role": "assistant", "display_text": display_text, "sql": "FAILED"})
            
        else:
            display_text = f"Here is what I found (Resolved in {attempts} attempt(s)):"
            st.success(display_text)
            with st.expander("View Generated SQL"):
                st.code(generated_sql, language="sql")
                
            results, columns = run_sql_query(generated_sql)
            if columns:
                st.dataframe([dict(zip(columns, row)) for row in results], use_container_width=True)
            else:
                st.info("Query executed successfully, but returned 0 results.")
                
            # Save the successful interaction to memory
            st.session_state.messages.append({"role": "assistant", "display_text": display_text, "sql": generated_sql})