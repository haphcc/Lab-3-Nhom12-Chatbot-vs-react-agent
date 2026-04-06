from .calculator_tool import calculate
from .factcheck_tool import fact_check
from .search_tool import web_search
from .wikipedia_tool import wikipedia_lookup


def suggest_tool(user_query: str) -> str:
    """
    Search-focused tool selection strategy for Agent Core.
    Return tool name that should be used first.
    """
    query = user_query.lower()
    if any(token in query for token in ["%", "cong", "tru", "nhan", "chia", "+", "-", "*", "/", "^"]):
        return "calculate"
    if any(token in query for token in ["kiem chung", "fact", "xac minh", "dung hay sai"]):
        return "fact_check"
    if any(token in query for token in ["dinh nghia", "la gi", "tieu su", "wiki", "wikipedia"]):
        return "wikipedia"
    return "search"


# Tool chaining examples:
# 1) search("gia vang hom nay") -> fact_check("gia vang hom nay")
# 2) search("dan so Viet Nam 2024") -> calculate("(430 - 514) / 514 * 100")
TOOLS = [
    {
        "name": "search",
        "func": web_search,
        "description": (
            "Tim kiem thong tin tren web tu mock data. Output la top ket qua lien quan "
            "(tieu de + snippet + source). Su dung khi can thong tin thoi su, su kien, du lieu moi nhat."
        ),
        "input_format": "string",
        "example": "search('Dan so Viet Nam 2024')",
    },
    {
        "name": "wikipedia",
        "func": wikipedia_lookup,
        "description": (
            "Lay thong tin tong quan tu Wikipedia mock. Output la summary ngan theo topic. "
            "Su dung khi can dinh nghia, boi canh lich su hoac kien thuc nen."
        ),
        "input_format": "string",
        "example": "wikipedia('Chien tranh Viet Nam')",
    },
    {
        "name": "calculate",
        "func": calculate,
        "description": (
            "Tinh toan toan hoc an toan tu bieu thuc string. Output la ket qua so. "
            "Su dung khi can so sanh so lieu, tinh phan tram, chuyen doi don vi."
        ),
        "input_format": "string (math expression)",
        "example": "calculate('(430 - 514) / 514 * 100')",
    },
    {
        "name": "fact_check",
        "func": fact_check,
        "description": (
            "Kiem tra tinh chinh xac cua mot phat bieu bang doi chieu nhieu nguon mock. "
            "Output dang True/False kem nguon tham khao. Su dung sau buoc search."
        ),
        "input_format": "string",
        "example": "fact_check('Viet Nam co 98 trieu dan nam 2024')",
    },
]


__all__ = [
    "TOOLS",
    "web_search",
    "wikipedia_lookup",
    "calculate",
    "fact_check",
    "suggest_tool",
]
