from openai import OpenAI
import re
import pandas as pd
from pyathena import connect

# ---------- OPENAI CLIENT ----------
client = OpenAI()

# ---------- AWS ATHENA CONNECTION ----------
conn = connect(
    aws_access_key_id="",
    aws_secret_access_key="",
    region_name="us-east-2",
    s3_staging_dir="s3://ai-sql-assistant-demo-sohel/query-results/",
    schema_name="ai_sql_demo"
)

# ---------- FETCH SCHEMA ----------
def get_schema():
    try:
        query = """
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = 'ai_sql_demo'
        """

        df = pd.read_sql(query, conn)

        schema = {}
        for _, row in df.iterrows():
            table = row['table_name']
            column = row['column_name']

            if table not in schema:
                schema[table] = []

            schema[table].append(column)

        return schema

    except Exception as e:
        return str(e)


# ---------- GENERATE SQL ----------
def generate_sql(question, history=[]):

    schema = get_schema()

    # Schema text
    schema_text = ""
    if isinstance(schema, dict):
        for table, cols in schema.items():
            schema_text += f"{table}({', '.join(cols)})\n"

    # History text
    history_text = ""
    for h in history[-3:]:
        history_text += f"User: {h['question']}\nSQL: {h.get('sql','')}\n"

    prompt = f"""
You are an expert SQL generator.

Your role:
- ONLY generate SQL queries
- If question is not SQL-related, say:
"I am an SQL assistant. I can only help with database-related questions."

DATABASE SCHEMA:
{schema_text}

CHAT HISTORY:
{history_text}

RULES:
- Use ONLY tables/columns from schema
- Maintain context from previous queries
- Return ONLY SQL
- No explanation
- End with semicolon

Question: {question}

SQL:
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You generate SQL queries using schema and context."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )

        output = response.choices[0].message.content.strip()

    except Exception as e:
        return f"LLM Error: {str(e)}"

    # ---------- SAFE HANDLING ----------
    if not output:
        return "No response from LLM"

    # Remove markdown formatting
    output = output.replace("```sql", "").replace("```", "").strip()

    # Guardrail: block non-SQL
    if not output.lower().startswith("select"):
        return output

    # Extract SQL
    match = re.search(r"SELECT.*?;", output, re.IGNORECASE | re.DOTALL)

    if match:
        return match.group(0)

    return "Could not generate SQL"


# ---------- RUN QUERY ----------
def run_query(sql):
    try:
        # 🚫 Prevent non-SQL execution
        if not sql.lower().startswith("select"):
            return sql

        df = pd.read_sql(sql, conn)
        return df

    except Exception as e:
        return str(e)