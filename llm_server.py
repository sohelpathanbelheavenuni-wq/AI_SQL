from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)
client = OpenAI()

@app.route("/generate-sql", methods=["POST"])
def generate_sql():
    data = request.json
    question = data.get("question")

    prompt = f"""
You are an SQL generator.
Return ONLY SQL query.

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