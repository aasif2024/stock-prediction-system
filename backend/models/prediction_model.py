"""
models/prediction_model.py
---------------------------------
Data-access functions for the `prediction_history` table.
"""

from database.db import db_cursor


def save_prediction(user_id: int, company_id: int, input_open: float, input_high: float,
                     input_low: float, input_close: float, input_traded_qty: int,
                     predicted_price: float, direction: str) -> int:
    with db_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO prediction_history
                (user_id, company_id, input_open, input_high, input_low,
                 input_close, input_traded_qty, predicted_price, direction)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (user_id, company_id, input_open, input_high, input_low,
             input_close, input_traded_qty, predicted_price, direction),
        )
        return cur.lastrowid


def get_predictions_for_user(user_id: int):
    with db_cursor() as cur:
        cur.execute(
            """
            SELECT ph.id, c.company_name, c.equity_name, ph.input_open, ph.input_high,
                   ph.input_low, ph.input_close, ph.input_traded_qty,
                   ph.predicted_price, ph.direction, ph.predicted_at
            FROM prediction_history ph
            JOIN companies c ON c.id = ph.company_id
            WHERE ph.user_id = %s
            ORDER BY ph.predicted_at DESC
            """,
            (user_id,),
        )
        return cur.fetchall()

def delete_prediction(user_id: int, prediction_id: int) -> bool:
    with db_cursor(commit=True) as cur:
        cur.execute(
            """
            DELETE FROM prediction_history
            WHERE id = %s AND user_id = %s
            """,
            (prediction_id, user_id)
        )
        return cur.rowcount > 0

