from sqlalchemy import create_engine, text, Connection

def connect_db() -> Connection:
    engine = create_engine('postgresql+psycopg2://postgres:password@recipes-db/recipes', echo=True)
    conn = engine.connect()

    return conn

def insert_recipes(conn: Connection, recipes: list[dict]):
    insert_into_tmp_table(conn, recipes)
    conn.execute(
        text("""MERGE INTO recipes r
                USING updates u
                ON r.title = u.title
                WHEN MATCHED THEN DO NOTHING
                WHEN NOT MATCHED BY TARGET THEN
                    INSERT VALUES (u.title, u.ingredients, u.method);
            """
        )
    )
    conn.commit()

def query_results(conn: Connection):
    results = conn.execute(text("SELECT * FROM recipes"))
    for row in results:
        print(f'title: {row.title}')
        print(f'ingredients: {row.ingredients}')
        print(f'method: {row.method}')
        print()

def insert_into_tmp_table(conn: Connection, recipes: list[dict]):
    conn.execute(
        text("""INSERT INTO updates (
                    title,
                    ingredients,
                    method
            ) VALUES (
                    :title,
                    :ingredients,
                    :method
            )"""
        ),
        [{
            "title": recipe["title"],
            "ingredients": recipe["ingredients"],
            "method": recipe["method"],
        } for recipe in recipes]
    )
    conn.commit()
