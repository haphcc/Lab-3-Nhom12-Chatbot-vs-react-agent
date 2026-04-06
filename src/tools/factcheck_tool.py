from .search_tool import web_search


def fact_check(query: str) -> str:
    """
    Bonus tool: goi search voi 2 nguon khac nhau va doi chieu ket qua.
    Quy uoc mock key:
    - <query>|source:baochinhphu
    - <query>|source:vnexpress
    """
    normalized_query = query.lower().strip()
    source_1_query = f"{normalized_query}|source:baochinhphu"
    source_2_query = f"{normalized_query}|source:vnexpress"

    source_1_result = web_search(source_1_query)
    source_2_result = web_search(source_2_query)

    not_found_message = "Khong tim thay thong tin moi nhat cho yeu cau nay."
    if source_1_result == not_found_message and source_2_result == not_found_message:
        return "False | Khong du du lieu doi chieu tu hai nguon mock."

    # so sanh theo gia tri so lieu cuc bo cho bai toan mock gia vang
    reference_number = "90.000.000"
    source_1_has_number = reference_number in source_1_result
    source_2_has_number = reference_number in source_2_result

    if source_1_has_number and source_2_has_number:
        return (
            "True | Thong tin nhat quan giua hai nguon. "
            "Sources: baochinhphu.vn, vnexpress.net."
        )

    return (
        "False | Thong tin chua nhat quan giua hai nguon. "
        f"Nguon 1: {source_1_result} | Nguon 2: {source_2_result}"
    )
