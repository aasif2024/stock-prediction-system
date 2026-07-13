from database.db import db_cursor

def add_to_watchlist(user_id: int, equity_name: str, shares: int = 0, buy_price: float = 0.0) -> dict:
    """Add a stock to the user's watchlist."""
    try:
        with db_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO watchlist (user_id, equity_name, shares, buy_price)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT(user_id, equity_name) DO UPDATE SET
                    shares = excluded.shares,
                    buy_price = excluded.buy_price
                """,
                (user_id, equity_name, shares, buy_price),
            )
            return {"status": "success", "message": f"{equity_name} added to watchlist."}
    except Exception as e:
        if "UNIQUE" in str(e).upper() or "Duplicate" in str(e):
            return {"status": "error", "message": f"{equity_name} is already in your watchlist."}
        raise e

def remove_from_watchlist(user_id: int, equity_name: str) -> dict:
    """Remove a stock from the user's watchlist."""
    with db_cursor(commit=True) as cur:
        cur.execute(
            """
            DELETE FROM watchlist
            WHERE user_id = %s AND equity_name = %s
            """,
            (user_id, equity_name),
        )
        return {"status": "success", "message": f"{equity_name} removed from watchlist."}

def get_watchlist(user_id: int) -> list:
    """Get the user's complete watchlist."""
    with db_cursor(commit=False) as cur:
        cur.execute(
            """
            SELECT equity_name, shares, buy_price, added_at
            FROM watchlist
            WHERE user_id = %s
            ORDER BY added_at DESC
            """,
            (user_id,),
        )
        return cur.fetchall()
