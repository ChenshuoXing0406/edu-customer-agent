from sqlalchemy import select

from app.core.database import session_scope
from app.models import KnowledgeItem
from app.schemas.knowledge import KnowledgeCreateRequest


def serialize_knowledge(item: KnowledgeItem) -> dict:
    return {
        "id": item.id,
        "title": item.title,
        "category": item.category,
        "keywords": item.keywords,
        "content": item.content,
    }


def load_knowledge() -> list[dict]:
    with session_scope() as session:
        items = session.scalars(select(KnowledgeItem).order_by(KnowledgeItem.created_at)).all()
        return [serialize_knowledge(item) for item in items]


def create_knowledge_id(category: str, existing_items: list[dict]) -> str:
    return f"{category}_{len(existing_items) + 1:03d}"


def create_knowledge(req: KnowledgeCreateRequest) -> dict:
    knowledge_items = load_knowledge()

    with session_scope() as session:
        item = KnowledgeItem(
            id=create_knowledge_id(req.category, knowledge_items),
            title=req.title,
            category=req.category,
            keywords=req.keywords,
            content=req.content,
        )
        session.add(item)
        session.flush()
        new_item = serialize_knowledge(item)

    return {
        "message": "knowledge_created",
        "item": new_item,
    }


def is_course_catalog_query(text: str) -> bool:
    catalog_phrases = [
        "有哪些课程",
        "有什么课程",
        "开设哪些课程",
        "课程列表",
        "都有什么课",
        "都有哪些课",
    ]

    return any(phrase in text for phrase in catalog_phrases)


WEAK_KEYWORDS = {
    "课程",
    "课",
    "报名",
    "适合",
}

GENERIC_COURSE_KEYWORDS = WEAK_KEYWORDS | {
    "零基础",
    "入门",
    "编程",
    "就业班",
    "应用开发",
    "五十音图",
}

INTENT_CATEGORY_MAP = {
    "price_consultation": "price",
    "trial_booking": "trial",
    "refund_policy": "refund",
    "account_issue": "account",
    "certificate_issue": "certificate",
    "course_consultation": "course",
}

MIN_RELIABLE_SCORE = 10


def get_item_course_entities(item: dict) -> set[str]:
    if item.get("category") != "course":
        return set()

    title = item["title"].lower()

    return {
        keyword.lower()
        for keyword in item.get("keywords", [])
        if keyword.lower() not in GENERIC_COURSE_KEYWORDS
        and keyword.lower() in title
    }


def get_query_course_entities(text: str, knowledge_items: list[dict]) -> set[str]:
    entities = set()

    for item in knowledge_items:
        entities.update(
            entity for entity in get_item_course_entities(item) if entity in text
        )

    return entities


def score_knowledge_item(
    message: str,
    intent: str,
    item: dict,
    query_course_entities: set[str] | None = None,
) -> int:
    text = message.lower()
    title = item["title"].lower()
    content = item["content"].lower()
    keywords = [keyword.lower() for keyword in item.get("keywords", [])]
    item_course_entities = get_item_course_entities(item)
    query_course_entities = query_course_entities or set()

    if (
        item.get("category") == "course"
        and query_course_entities
        and not item_course_entities.intersection(query_course_entities)
    ):
        return 0

    score = 0
    has_reliable_match = False

    for keyword in keywords:
        if keyword not in text:
            continue

        if keyword in WEAK_KEYWORDS:
            score += 1
        else:
            score += 4
            has_reliable_match = True

        if keyword in title:
            score += 5

        if keyword in content:
            score += 1

    matched_course_entities = item_course_entities.intersection(query_course_entities)

    if matched_course_entities:
        score += 10 * len(matched_course_entities)
        has_reliable_match = True

    expected_category = INTENT_CATEGORY_MAP.get(intent)

    if has_reliable_match and item.get("category") == expected_category:
        score += 12

    if not has_reliable_match:
        return 0

    return score


def retrieve_knowledge(message: str, intent: str, top_k: int = 2) -> list[dict]:
    knowledge_items = load_knowledge()
    text = message.lower()

    if is_course_catalog_query(text):
        return [
            item for item in knowledge_items if item.get("category") == "course"
        ][:top_k]

    query_course_entities = get_query_course_entities(text, knowledge_items)
    scored_items = []

    for item in knowledge_items:
        score = score_knowledge_item(message, intent, item, query_course_entities)

        if score > 0:
            scored_items.append((score, item))

    scored_items.sort(key=lambda x: x[0], reverse=True)

    if not scored_items:
        return []

    top_score = scored_items[0][0]

    if top_score < MIN_RELIABLE_SCORE:
        return []

    filtered_items = []

    for score, item in scored_items:
        if score >= MIN_RELIABLE_SCORE:
            filtered_items.append(item)

    return filtered_items[:top_k]
