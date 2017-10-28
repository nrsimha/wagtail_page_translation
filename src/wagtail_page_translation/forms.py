from __future__ import absolute_import, unicode_literals

from operator import itemgetter

from django import forms
from django.conf import settings
from django.utils.translation import ugettext as _
from wagtail.wagtailcore.models import Page
from wagtail.wagtailadmin import widgets

from .models import Language


class LanguageForm(forms.ModelForm):
    """Custom language form.

    Using a custom form which sets the choices for the `code`
    field prevents us to have new migrations when settings change.
    """
    code = forms.ChoiceField(
        label=_("Language"), choices=settings.LANGUAGES,
        help_text=_("One of the languages defined in LANGUAGES"))

    class Meta:
        model = Language
        fields = (
            'code',
            'is_default',
            'order',
            'live',
        )

    def __init__(self, *args, **kwargs):
        super(LanguageForm, self).__init__(*args, **kwargs)

        # Sort language choices according their display name
        sorted_choices = sorted(self.fields['code'].choices, key=itemgetter(1))
        self.fields['code'].choices = sorted_choices


class AddTranslationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        # CopyPage must be passed a 'page' kwarg indicating the page to be
        # copied
        self.page = kwargs.pop('page')
        can_publish = kwargs.pop('can_publish')
        parent_page = kwargs.pop('parent_page')
        super(AddTranslationForm, self).__init__(*args, **kwargs)
        # parent_page = self.page.get_parent()
        self.fields['new_title'] = forms.CharField(
            initial=self.page.title, label=_("New title"))
        self.fields['new_slug'] = forms.SlugField(
            initial=self.page.slug, label=_("New slug"))
        self.fields['new_parent_page'] = forms.ModelChoiceField(
            initial=parent_page,  # self.page.get_parent(),
            queryset=Page.objects.all(),
            widget=widgets.AdminPageChooser(can_choose_root=True),
            label=_("New parent page"),
            help_text=_("This copy will be a child of this given parent page.")
        )

        # pages_to_copy = self.page.get_descendants(inclusive=True)
        # subpage_count = pages_to_copy.count() - 1
        # if subpage_count > 0:
        #     self.fields['copy_subpages'] = forms.BooleanField(
        #         required=False, initial=True, label=_("Copy subpages"),
        #         help_text=ungettext(
        #             "This will copy %(count)s subpage.",
        #             "This will copy %(count)s subpages.",
        #             subpage_count) % {'count': subpage_count})

        if can_publish:
            label = _("Publish copied page")
            help_text = _("This page is live. Would you like to publish its "
                          "copy as well?")
            self.fields['publish_copies'] = forms.BooleanField(
                required=False, initial=True, label=label, help_text=help_text
            )

    def clean(self):
        cleaned_data = super(AddTranslationForm, self).clean()

        # Make sure the slug isn't already in use
        slug = cleaned_data.get('new_slug')

        # New parent page given in form or parent of source, if parent_page
        # is empty
        parent_page = cleaned_data.get('new_parent_page') or \
            self.page.get_parent()

        # Count the pages with the same slug within the context of our copy's
        # parent page
        if slug and parent_page.get_children().filter(slug=slug).count():
            self._errors['new_slug'] = self.error_class(
                [_("This slug is already in use within the context of its "
                   "parent page \"%s\"" % parent_page)]
            )
            # The slug is no longer valid, hence remove it from cleaned_data
            del cleaned_data['new_slug']

        return cleaned_data
