import uuid

from django.conf import settings
from django.db import models
from django.http import Http404
from django.shortcuts import redirect
from django.utils.encoding import force_text
from django.utils.translation import activate, ugettext_lazy as _

from wagtail.wagtailcore.models import Page
from wagtail.wagtailadmin.edit_handlers import FieldPanel, MultiFieldPanel

from .managers import LanguageManager


class Language(models.Model):
    code = models.CharField(
        max_length=12,
        help_text="One of the languages defined in LANGUAGES")

    is_default = models.BooleanField(
        default=False, help_text="""
        Visitors with no language preference will see the site in this
        language
        """)

    order = models.IntegerField(
        default=0,
        help_text="""
        Language choices and translations will be displayed in this order
        """)

    live = models.BooleanField(
        default=True,
        help_text="Is this language available for visitors to view?")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return force_text(dict(settings.LANGUAGES).get(self.code))

    objects = LanguageManager()
    # def has_pages_in_site(self, site):
    #     return (
    #         self.pages.filter(
    #             path__startswith=site.root_page.path
    #         ).exists())


def _language_default():
    # Let the default return a PK, so migrations can also work with this value.
    # The FakeORM model in the migrations differ from this Django model.
    default_language = Language.objects.default()
    if default_language is None:
        return None
    else:
        return default_language.pk


class TranslatablePage(Page):
    # Explicitly defined with a unique name so that clashes are unlikely
    translatable_page_ptr = models.OneToOneField(
        Page, parent_link=True, related_name='+', on_delete=models.CASCADE)

    # Pages with identical translation_keys are translations of each other
    # Users can change this through the admin UI, although the raw UUID
    # value should never be shown.
    translation_key = models.UUIDField(db_index=True, default=uuid.uuid4)

    # Deleting a language that still has pages is not allowed, as it would
    # either lead to tree corruption, or to pages with a null language.
    language = models.ForeignKey(Language, on_delete=models.PROTECT,
                                 default=_language_default)
    # Language, related_name='pages', on_delete=models.PROTECT,

    def serve(self, request, *args, **kwargs):
        activate(self.language.code)
        request.LANGUAGE_CODE = self.language.code
        return super(TranslatablePage, self).serve(request, *args, **kwargs)

    class Meta:
        pass
        # # This class is *not* abstract, so that the unique_together
        # # constraint holds across all page classes. Translations of a page
        # # do not have to be of the same page type.
        #
        # unique_together = [
        #     # Only one language allowed per translation group
        #     ('translation_key', 'language'),
        # ]

    is_creatable = False

    settings_panels = Page.settings_panels + [
        MultiFieldPanel(
            heading=_("Translations"),
            children=[
                FieldPanel('language'),
            ]
        ),
    ]

    # base_form_class = AdminTranslatablePageForm

    def get_admin_display_title(self):
        return "{} ({})".format(self.title, self.language)

    def get_translations(self, only_live=True):
        """Get all translations of this page.

        This page itself is not included in the result, all pages
        are sorted by the language position.

        :param only_live: Boolean to filter on live pages & languages.
        :return: TranslatablePage instance

        """
        # canonical_page_id = self.canonical_page_id or self.pk
        translations = TranslatablePage.objects.filter(
            translation_key=self.translation_key).exclude(pk=self.pk)

        if only_live:
            translations = translations.live().filter(language__live=True)

        return translations.order_by('language__order')

    def has_translation(self, language):
        """Check if page isn't already translated in given language.

        :param language: Language instance
        :return: Boolean

        """
        return TranslatablePage.objects.filter(
            translation_key=self.translation_key, language=language).exists()

    def get_translation(self, language):
        """Get translated page for given language.

        :param language: Language instance
        :return: Boolean

        """
        return TranslatablePage.objects.filter(
            translation_key=self.translation_key, language=language).\
            specific().last()

    def get_translation_from_code(self, language_code):
        language = Language.objects.get(code=language_code)
        return self.get_translation(language)

    def get_translation_parent(self, language):
        site = self.get_site()
        if not language.has_pages_in_site(site):
            return site.root_page

        translation_parent = (
            TranslatablePage.objects
            .filter(
                translation_key=self.get_parent().translation_key,
                language=language,
                path__startswith=site.root_page.path
            ).first())
        return translation_parent

    # @cached_property
    # def has_translations(self):
    #     return self.translations.exists()
    #
    # @cached_property
    # def is_canonical(self):
    #     return not self.canonical_page_id and self.has_translations


def get_user_languages(request):
    """
    Get the best matching Languages for a request, in order from best to worst.
    The default language (if there is one) will always appear in this list.
    """
    return [Language.objects.default()]


class AbstractTranslationIndexPage(Page):
    """Abstract root page of any translatable site.

    This page should be used as the root page because it will
    route the requests to the right language.
    """

    def serve(self, request, *args, **kwargs):
        """Serve TranslatablePage in the correct language

        :param request: request object
        :return: Http403 or Http404

        """
        languages = get_user_languages(request)
        candidates = TranslatablePage.objects.live().specific().child_of(self)
        for language in languages:
            try:
                translation = candidates.filter(language=language).get()
                return redirect(translation.url)
            except TranslatablePage.DoesNotExist:
                continue

        # No translation was found, not even in the default language.
        raise Http404

    class Meta:
        abstract = True
