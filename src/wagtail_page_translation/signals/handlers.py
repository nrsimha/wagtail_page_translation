from django.dispatch import receiver

from wagtail.wagtailadmin.signals import init_new_page

from ..models import TranslatablePage


@receiver(init_new_page)
def add_language_from_parent(sender, **kwargs):
    if (isinstance(kwargs['parent'], TranslatablePage) and
            isinstance(kwargs['page'], TranslatablePage)):
        if kwargs['parent'] and kwargs['parent'].language:
            kwargs['page'].language = kwargs['parent'].language
