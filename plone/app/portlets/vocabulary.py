# -*- coding: utf-8 -*-
"""Vocabulary of styles."""

from plone.app.portlets import PloneMessageFactory as _
from plone.app.portlets.styles import EmptyLineError
from plone.app.portlets.styles import InvalidCssClassError
from plone.app.portlets.styles import parse_style
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from zope.interface import implements
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

import logging

logger = logging.getLogger(__name__)


class StylesVocabulary(object):
    """Vocabulary factory of portlet styles read from control panel registry."""
    implements(IVocabularyFactory)

    def __call__(self, context):
        registry = getUtility(IRegistry)
        try:
            styles = registry['plone.app.portlets.browser.interfaces.IPortletStyles.portlet_styles']
        except KeyError:
            # if portlet_styles field is not found in plone.app.registry, just
            # return an empty list -> probably the product is registered (zcml)
            # but not installed (GenericSetup)
            styles = []

        # always have the default "default style" option available, which is effectively a no-op
        terms = [SimpleTerm(title=_(u"Default style"), value=" ")]

        # add styles from the control panel, but filter out invalid ones
        for style in styles:

            try:
                css, title = parse_style(style)
            except EmptyLineError:
                continue
            except InvalidCssClassError:
                logger.warn("Filtered out a style because it doesn't have a valid CSS class: '%s'" % style)
                continue
            except:
                logger.warn("Filtered out a style because it cannot be parsed: '%s'" % style)
                continue

            terms.append(SimpleTerm(title=title, value=css))

        # if a portlet has a style assigned that is no longer listed in
        # portlet_styles, than we need to add it to the drop-down menu,
        # so it's still possible to select it
        if hasattr(context, 'portlet_style') and not context.portlet_style in [t.value for t in terms]:
            terms.append(SimpleTerm(
                    title=context.portlet_style,
                    value=context.portlet_style,
                ))

        return SimpleVocabulary(terms)


StylesVocabularyFactory = StylesVocabulary()
