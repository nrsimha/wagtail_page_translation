from django import template

from ..models import Language, TranslatablePage


register = template.Library()


@register.simple_tag(takes_context=True)
def get_languages(context, record):

    # generate list of links for each language
    languages = {
        'list': []
    }

    live_languages = Language.objects.all().filter(live=True)

    # for non Wagtail pages
    if not record:
        url_split = context['request'].path.split('/')
        current_language = context['LANGUAGE_CODE']
        for language in live_languages:
            # create special record for current language
            if language.code == current_language:
                languages['current'] = {
                    'code': language.code,
                    'name': str(language)}
            url_split[1] = language.code
            languages['list'].append({
                'is_translated': True,
                'code': language.code,
                'name': str(language),
                'url': '/'.join(url_split),
            })
        return languages

    # for Wagtail pages
    view_slug = None
    if 'view_slug' in context:
        view_slug = context['view_slug']

    pages = []
    if hasattr(record, 'language'):
        pages = TranslatablePage.objects.live(). \
            filter(translation_key=record.translation_key).specific()

    available_languages = []
    translated_pages = {}

    for page in pages:
        available_languages.append(page.language)
        # translated_pages[page.language] = page.url
        translated_pages[page.language.code] = page.url
        if view_slug:
            if view_slug != 'side_by_side':
                translated_pages[page.language.code] += page.reverse_subpage(
                    view_slug)

    for language in live_languages:
        # create special record for current language
        if language == record.language:
            languages['current'] = {
                'code': language.code,
                'name': str(language)}
        if language in available_languages:
            languages['list'].append({
                'is_translated': True,
                'code': language.code,
                'name': str(language),
                'url': translated_pages[language.code],
            })
        else:
            # use frontpage when record for that language is not translated
            languages['list'].append({
                'is_translated': None,
                'code': language.code,
                'name': str(language),
                'url': '/%s/' % language.code})
    return languages
