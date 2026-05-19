import ollama
import sqlite3
import time

DB_NAME = "inventory_database.db"
MODEL_NAME = "qwen2.5-coder:1.5b"

# 1. The Golden Dataset
test_cases = [
    # EASY
    {"id": 1, "level": "Easy", "q": "Show me all customers who live in Dhaka.", "expected": "SELECT customer_name FROM Customers WHERE city = 'Dhaka';"},
    {"id": 2, "level": "Easy", "q": "Show me all the customers residing in Dhaka.", "expected": "SELECT customer_name FROM Customers WHERE city = 'Dhaka';"},
    {"id": 3, "level": "Easy", "q": "Can you show me all the products delivered to Dhaka?", "expected": "UNANSWERABLE"},
    
    # MEDIUM
    {"id": 4, "level": "Medium", "q": "What are the names of the 2 cheapest products?", "expected": "SELECT product_name FROM Products ORDER BY price ASC LIMIT 2;"},
    {"id": 5, "level": "Medium", "q": "What are the 2 cheapest products we have in our inventory?", "expected": "SELECT product_name FROM Products ORDER BY price ASC LIMIT 2;"},
    {"id": 6, "level": "Medium", "q": "What are our top 2 products which cost the least?", "expected": "SELECT product_name FROM Products ORDER BY price ASC LIMIT 2;"},
    
    # HARD
    {"id": 7, "level": "Hard", "q": "Which products have a price that is above the average price of all products?", "expected": "SELECT product_name FROM Products WHERE price > (SELECT AVG(price) FROM Products);"},
    {"id": 8, "level": "Hard", "q": "What are the products with prices more than the average price?", "expected": "SELECT product_name FROM Products WHERE price > (SELECT AVG(price) FROM Products);"},
    {"id": 9, "level": "Hard", "q": "Does any product exceed the average price range?", "expected": "SELECT product_name FROM Products WHERE price > (SELECT AVG(price) FROM Products);"}
]

# 2. The Silent SQLite Tester
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

# 3. The Q1 Methodological Engine (Self-Correction)
def generate_with_self_correction(user_query, max_retries=3):
    schema = """
    Table: Customers (customer_id, customer_name, city)
    Table: Products (product_id, product_name, price, stock_quantity)
    """
    
    system_prompt = f"""You are a strict SQLite expert. 
    Rule 1: Return ONLY valid SQL. 
    Rule 2: Do NOT use tables or columns that do not exist in the schema. 
    Rule 3: If the question CANNOT be answered with the provided schema, return exactly the word: UNANSWERABLE.
    Schema:\n{schema}"""
    
    conversation_history = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': user_query}
    ]
    
    for attempt in range(1, max_retries + 1):
        response = ollama.chat(model=MODEL_NAME, messages=conversation_history)
        ai_sql = response['message']['content'].replace("```sql", "").replace("```", "").strip()
        
        # Check Escape Hatch
        if "UNANSWERABLE" in ai_sql.upper():
            return "UNANSWERABLE", attempt
            
        conversation_history.append({'role': 'assistant', 'content': ai_sql})
        is_valid, error_msg = test_sql_silently(ai_sql)
        
        if is_valid:
            return ai_sql, attempt
        else:
            if attempt < max_retries:
                correction_prompt = f"Executing that SQL gave this SQLite error: '{error_msg}'. Fix this error. Remember you ONLY have the Customers and Products tables. If it's impossible, reply with UNANSWERABLE."
                conversation_history.append({'role': 'user', 'content': correction_prompt})
            else:
                return f"FAILED AFTER {max_retries} RETRIES", attempt

# 4. The Automated Test Runner
print(f"Starting Q1 Benchmark Test with Self-Correction...\n" + "="*60)

total_start_time = time.time()

for test in test_cases:
    print(f"Running Test {test['id']} ({test['level']})...")
    
    start_time = time.time()
    final_sql, attempts = generate_with_self_correction(test["q"])
    latency = time.time() - start_time
    
    print(f"Question: {test['q']}")
    print(f"Expected: {test['expected']}")
    print(f"AI Result: {final_sql}")
    
    # Grading Logic
    if final_sql == "UNANSWERABLE" and test["expected"] == "UNANSWERABLE":
         print("Grade: ✅ PASS (Correctly rejected impossible query)")
    elif "FAILED" in final_sql:
         print("Grade: ❌ FAIL (Could not generate valid SQL)")
    else:
         print("Grade: ✅ PASS (Valid SQL Generated)")
         
    print(f"Attempts Needed: {attempts}")
    print(f"Time taken: {latency:.2f} seconds\n" + "-"*60)

print(f"Benchmark Complete! Total Execution Time: {time.time() - total_start_time:.2f} seconds")