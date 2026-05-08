from langchain_community.utilities import SQLDatabase
from langchain_community.llms import Ollama
from langchain.chains import create_sql_query_chain
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool

# Import the existing database url from your db.py
from db import DATABASE_URL

def get_sql_query_from_text(question: str, model_name="llama3.2:1b"):
    """
    Takes a natural language question and returns ONLY the generated SQL query.
    Uses your local Ollama LLM setup.
    """
    # Connect to the database using Langchain's wrapper
    db = SQLDatabase.from_uri(DATABASE_URL)
    
    # Initialize the LLM (assuming you are using Ollama locally based on previous projects)
    llm = Ollama(model=model_name, temperature=0)
    
    # Create the text-to-SQL chain
    chain = create_sql_query_chain(llm, db)
    
    # Invoke the chain with the user's question
    response = chain.invoke({"question": question})
    return response

def get_answer_from_text(question: str, model_name="llama3.2:1b"):
    """
    Takes a natural language question, generates the SQL, executes it on the DB, 
    and returns the raw result.
    """
    db = SQLDatabase.from_uri(DATABASE_URL)
    llm = Ollama(model=model_name, temperature=0)
    
    # Tool to execute the generated query
    execute_query = QuerySQLDataBaseTool(db=db)
    
    # Tool to write the query
    write_query = create_sql_query_chain(llm, db)
    
    # Chain them together: write the query -> execute the query
    chain = write_query | execute_query
    
    response = chain.invoke({"question": question})
    return response

def generate_dashboard_component(prompt: str, model_name="llama3.2:1b"):
    """
    Generates both a SQL query and a recommended chart type (line, bar, or pie).
    """
    from langchain_community.llms import Ollama
    from langchain_community.utilities import SQLDatabase
    import json
    import re
    
    db = SQLDatabase.from_uri(DATABASE_URL)
    llm = Ollama(model=model_name, temperature=0)
    
    schema = db.get_table_info()
    
    system_prompt = f"""
    You are a PostgreSQL expert. Given the database schema below, generate a valid PostgreSQL query and a recommended chart type.
    The chart type MUST be one of: "line", "bar", or "pie".

    CRITICAL POSTGRESQL RULES:
    1. When using GROUP BY, every column in the SELECT list that is not an aggregate function (like SUM, COUNT, AVG) MUST be included in the GROUP BY clause.
    2. If the user asks for "sales", "revenue", or "total", you MUST use an aggregate function like SUM(column_name).
    3. If the user asks for "distribution" or "count", use COUNT(*).
    4. Ensure the SQL is valid PostgreSQL syntax.

    Schema:
    {schema}

    Respond ONLY with a JSON object. No conversational text.
    Example:
    {{
        "query": "SELECT category, SUM(sales) as total_sales FROM sales_data GROUP BY category",
        "chart_type": "bar"
    }}
    """
    
    user_prompt = f"User Request: {prompt}"
    
    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    response = llm.invoke(full_prompt)
    
    try:
        # Extract JSON using regex in case the LLM adds conversational filler
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return json.loads(response)
    except Exception:
        # Fallback to the basic SQL generation if JSON parsing fails
        return {
            "query": get_sql_query_from_text(prompt, model_name),
            "chart_type": "bar"
        }
