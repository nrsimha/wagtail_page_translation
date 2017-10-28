from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import ugettext as _

from wagtail.wagtailadmin import messages
from wagtail.wagtailadmin.views.pages import get_valid_next_url_from_request
from wagtail.wagtailcore.models import Page

from ..models import Language, TranslatablePage
from ..forms import AddTranslationForm


def add_translation(request, page_id, language_code):
    page = TranslatablePage.objects.get(id=page_id)

    new_language = Language.objects.get(code=language_code)

    parent_page = page.get_parent().specific
    if hasattr(parent_page, 'get_translation'):
        # Parent page defaults to parent of source page
        parent_page = parent_page.get_translation(new_language)

    # Check if the user has permission to publish subpages on the parent
    can_publish = parent_page.permissions_for_user(request.user). \
        can_publish_subpage()

    # Create the form
    form = AddTranslationForm(request.POST or None, page=page,
                              can_publish=can_publish,
                              parent_page=parent_page)

    next_url = get_valid_next_url_from_request(request)

    # Check if user is submitting
    if request.method == 'POST':
        # Prefill parent_page in case the form is invalid (as prepopulated
        # value for the form field, because ModelChoiceField seems to not
        # fall back to the user given value)
        parent_page = Page.objects.get(id=request.POST['new_parent_page'])

        if form.is_valid():
            # Receive the parent page (this should never be empty)
            if form.cleaned_data['new_parent_page']:
                parent_page = form.cleaned_data['new_parent_page']

            # Make sure this user has permission to add subpages on the parent
            if not parent_page.permissions_for_user(request.user).\
                    can_add_subpage():
                raise PermissionDenied

            # Re-check if the user has permission to publish subpages on the
            # new parent
            can_publish = parent_page.permissions_for_user(request.user).\
                can_publish_subpage()

            # Copy the page
            page.copy(
                # recursive=form.cleaned_data.get('copy_subpages'),
                to=parent_page,
                update_attrs={
                    'title': form.cleaned_data['new_title'],
                    'slug': form.cleaned_data['new_slug'],
                    'language': new_language,
                },
                keep_live=(can_publish and
                           form.cleaned_data.get('publish_copies')),
                user=request.user,
            )

            # Give a success message back to the user
            messages.success(request,
                             _("Page '{0}' translated.").format(
                                 page.get_admin_display_title()))

            # Redirect to explore of parent page
            if next_url:
                return redirect(next_url)
            return redirect('wagtailadmin_explore', parent_page.id)

    return render(
        request,
        'wagtail_page_translation/translation/add_translation.html', {
            'page': page,
            'new_language': new_language,
            'form': form,
            'next': next_url,
        })


def revisions_index(request, page_id):
    page = get_object_or_404(Page, id=page_id).specific
    languages = []

    for language in Language.objects.all():
        languages.append({
            'language': language,
            'translation': page.get_translation(language)
        })

    page_perms = page.permissions_for_user(request.user)
    return render(request, 'wagtail_page_translation/translation/index.html', {
        'page': page,
        'page_perms': page_perms,
        'languages': languages,
    })
