from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class WagtailPageTranslationConfig(AppConfig):

    name = 'wagtail_page_translation'
    verbose_name = _("Wagtail Page Translation")
