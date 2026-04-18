from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)
client = OpenAI()

@app.route("/generate-sql", methods=["POST"])
def generate_sql():
    data = request.json
    question = data.get("question")

    prompt = f"""
You are an expert SQL generator.
ONLY use the following schema:
Database: ai_sql_demo
Tables:
1. customers
- customer_id
- customer_name
- country
2. salesdata
- order_id
- customer
- product
- sales
- region
3. products
- product_id
- product_name
- category
RULES:
- Use ONLY these tables and columns
- Do NOT invent column names
- Use correct joins when needed
- Return ONLY SQL query
- No explanation

Question: {question}
SQL:
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        sql = response.choices[0].message.content.strip()

        return jsonify({"sql": sql})

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
