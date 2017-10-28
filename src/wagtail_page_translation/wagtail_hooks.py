from django.conf.urls import include, url
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from wagtail.wagtailadmin.menu import MenuItem
from wagtail.wagtailcore import hooks
from wagtail.wagtailadmin.widgets import Button

from .urls import languages, translations


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^language/', include(
            languages, namespace='wagtail_page_translation_languages')),
        url(r'^translate/',
            include(translations, namespace='wagtail_page_translation')),
    ]


@hooks.register('register_settings_menu_item')
def register_language_menu_item():
    return MenuItem(
        'Languages',
        reverse('wagtail_page_translation_languages:index'),
        classnames='icon icon-snippet',
        order=1000,
    )


@hooks.register('register_page_listing_more_buttons')
def page_listing_more_buttons(page, page_perms, is_parent=False):
    if not hasattr(page, 'language'):
        return
    # if page_perms.can_move():
    if not page.is_root():
        yield Button(_('Translations'),
                     reverse('wagtail_page_translation:index', args=[page.id]),
                     attrs={'title': _("View this page's translations")},
                     priority=50)
