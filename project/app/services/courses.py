def recommend_course_slug(age: int | None, target: str | None) -> str:
    if age is not None and age <= 15:
        return "kazkids"
    if target in ("gov", "business"):
        return "qyzmet-qazaq"
    return "kazpro"
