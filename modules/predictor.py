from modules.db import get_db_connection


def predict_colleges(rank, exam=None, counselling=None):

    conn = get_db_connection()

    query = """
        SELECT *
        FROM colleges
        WHERE closing_rank >= ?
    """

    params = [rank]

    if exam:
        query += " AND exam_type = ?"
        params.append(exam)

    if counselling:
        query += " AND counselling_system = ?"
        params.append(counselling)

    query += " ORDER BY closing_rank ASC"

    colleges = conn.execute(query, params).fetchall()

    conn.close()

    return colleges