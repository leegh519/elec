"""분류 검증과 제본 순서의 단일 기준. 브라우저/PDF의 문항 ID는 바꾸지 않는다."""
from __future__ import annotations


def indexes(taxonomy):
    categories, topics, subtopics = {}, {}, {}
    for ci, category in enumerate(taxonomy['categories']):
        categories[category['id']] = (ci, category)
        for ti, topic in enumerate(category['topics']):
            topics[topic['id']] = (category['id'], ti, topic)
            for si, subtopic in enumerate(topic.get('subtopics', [])):
                if subtopic['id'] in subtopics:
                    raise ValueError(f"중복 소분류: {subtopic['id']}")
                subtopics[subtopic['id']] = (category['id'], topic['id'], si, subtopic)
    return categories, topics, subtopics


def validate_classification(classification, taxonomy):
    categories, topics, subtopics = indexes(taxonomy)
    category = classification['category']
    primary = classification['primaryTopic']
    leaf = classification['primarySubtopic']
    if category not in categories or primary not in topics or leaf not in subtopics:
        raise ValueError('존재하지 않는 대표 분류')
    if subtopics[leaf][:2] != (category, primary):
        raise ValueError('대표 대·중·소분류 불일치')
    if classification['topics'][0] != primary or classification['subtopics'][0] != leaf:
        raise ValueError('대표 분류는 목록의 첫 항목이어야 합니다')
    expected_topics = list(dict.fromkeys(subtopics[s][1] for s in classification['subtopics']))
    if expected_topics != classification['topics']:
        raise ValueError('관련 중분류와 소분류 불일치')
    if any(subtopics[s][0] != category for s in classification['subtopics']):
        raise ValueError('관련 소분류의 대분류 불일치')
    tag_ids = {t['id'] for t in taxonomy['studyTags']}
    if not classification['tags'] or not set(classification['tags']) <= tag_ids:
        raise ValueError('존재하지 않는 태그')
    if classification['primaryTag'] not in classification['tags']:
        raise ValueError('대표 태그 누락')
    for key in ['topics', 'subtopics', 'tags']:
        if len(classification[key]) != len(set(classification[key])):
            raise ValueError(f'중복 {key}')


def build_print_plan(questions, taxonomy, *, categories=None, topics=None,
                     subtopics=None, tags=None, group_by='subtopic', tag_priority=None):
    """대분류→대표 중분류→대표 소분류/태그→연도/시험 순. ID당 1회 수록."""
    cats, mids, leaves = indexes(taxonomy)
    tag_map = {t['id']: (i, t['label']) for i, t in enumerate(taxonomy['studyTags'])}
    if group_by not in {'subtopic', 'tag'}:
        raise ValueError('group_by는 subtopic 또는 tag여야 합니다')
    for requested, valid, label in [(categories, cats, '대분류'), (topics, mids, '중분류'),
                                     (subtopics, leaves, '소분류'), (tags, tag_map, '태그'),
                                     (tag_priority, tag_map, '우선 태그')]:
        if requested and not set(requested) <= set(valid):
            raise ValueError(f"존재하지 않는 {label}: {sorted(set(requested) - set(valid))}")
    unique = {}
    for q in questions:
        if q['id'] in unique and q != unique[q['id']]:
            raise ValueError(f"내용이 다른 중복 문항: {q['id']}")
        unique[q['id']] = q
    selected = []
    for q in unique.values():
        cl = q['classification']
        validate_classification(cl, taxonomy)
        if categories and cl['category'] not in categories:
            continue
        if topics and not set(cl['topics']).intersection(topics):
            continue
        if subtopics and not set(cl['subtopics']).intersection(subtopics):
            continue
        if tags and not set(cl['tags']).intersection(tags):
            continue
        selected.append(q)
    agencies = {'국가직': 0, '지방직': 1, '군무원': 2, '국회직': 3, '서울시': 4}

    def tag_for(q):
        cl = q['classification']
        return next((t for t in tag_priority or [] if t in cl['tags']), cl['primaryTag'])

    def key(q):
        cl = q['classification']
        prefix = (cats[cl['category']][0], mids[cl['primaryTopic']][1])
        sub_order = leaves[cl['primarySubtopic']][2]
        group_order = (sub_order,) if group_by == 'subtopic' else (tag_map[tag_for(q)][0], sub_order)
        return (*prefix, *group_order, q['year'], agencies.get(q['agency'], 99), q['number'], q['id'])

    selected.sort(key=key)
    plan = []
    for i, q in enumerate(selected):
        cl = q['classification']
        group = cl['primarySubtopic'] if group_by == 'subtopic' else tag_for(q)
        plan.append({'sequence': i + 1, 'page': i // 4 + 1, 'slot': i % 4 + 1,
                     'id': q['id'], 'category': cl['category'], 'categoryLabel': cats[cl['category']][1]['label'],
                     'topic': cl['primaryTopic'], 'topicLabel': mids[cl['primaryTopic']][2]['label'],
                     'subtopic': cl['primarySubtopic'], 'subtopicLabel': leaves[cl['primarySubtopic']][3]['label'],
                     'group': group, 'groupLabel': leaves[group][3]['label'] if group_by == 'subtopic' else tag_map[group][1],
                     'tags': cl['tags'], 'source': f"{q['year']} {q['agency']} {q['number']}번",
                     'answer': q['answer']['choice']})
    return plan
