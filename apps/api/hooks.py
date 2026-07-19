"""drf-spectacular preprocessing hook: barcha endpointlarga ?lang parametrini qo‘shadi."""

LANG_PARAM = {
    'name': 'lang',
    'in': 'query',
    'required': False,
    'description': 'Kontent tili: uz (standart), uz-cyrl, ru, en',
    'schema': {'type': 'string', 'enum': ['uz', 'uz-cyrl', 'ru', 'en']},
}


def preprocess_add_lang(result, generator, request, public, **kwargs):
    """OpenAPI natijasidagi har bir operatsiyaga lang parametrini kiritadi."""
    for path, methods in result.get('paths', {}).items():
        if not path.startswith('/api/v1/'):
            continue
        for method, op in methods.items():
            params = op.setdefault('parameters', [])
            if not any(p.get('name') == 'lang' for p in params):
                params.append(LANG_PARAM)
    return result
