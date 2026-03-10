from sqlalchemy import create_engine, text

engine = create_engine('postgresql+psycopg2://benjamingraham:@localhost:5432/recipes', echo=True)
with engine.begin() as conn:
    conn.execute(text('DELETE FROM recipes'))