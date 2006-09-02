from zope.interface import implements
from zope.component import getMultiAdapter, getUtility
from zope.app.container.interfaces import INameChooser

from Products.Five import BrowserView
from Acquisition import aq_base

from Products.CMFCore.utils import getToolByName

from plone.portlets.interfaces import IPortletManager
from plone.portlets.interfaces import IPortletAssignmentMapping
from plone.portlets.interfaces import ILocalPortletAssignmentManager

from plone.portlets.constants import USER_CATEGORY
from plone.portlets.constants import GROUP_CATEGORY
from plone.portlets.constants import CONTENT_TYPE_CATEGORY
from plone.portlets.constants import CONTEXT_CATEGORY

from plone.app.portlets.portlets.classic import ClassicPortletAssignment
from plone.app.portlets.portlets.login import LoginPortletAssignment

from plone.app.portlets.storage import PortletAssignmentMapping

from plone.app.portlets.browser.interfaces import IManagePortletsView
from plone.app.portlets.browser.interfaces import IManageContextualPortletsView
from plone.app.portlets.browser.interfaces import IManageCurrentUserPortletsView

class ManageContextualPortlets(BrowserView):
    implements(IManageContextualPortletsView)
        
    # IManagePortletsView implementation
    
    def getAssignmentMappingUrl(self, manager):
        baseUrl = str(getMultiAdapter((self.context, self.request), name='absolute_url'))
        return '%s/++contextportlets++%s' % (baseUrl, manager.__name__)
    
    def getAssignmentsForManager(self, manager):
        assignments = getMultiAdapter((self.context, manager), IPortletAssignmentMapping)
        return assignments.values()
    
    # view @@manage-portlets
    
    def has_legacy_portlets(self):
        left_slots = getattr(aq_base(self.context), 'left_slots', [])
        right_slots = getattr(aq_base(self.context), 'right_slots', [])
        
        return left_slots or right_slots

    # view @@set-portlet-blacklist-status
    def set_blacklist_status(self, manager, user_status, group_status, content_type_status, context_status):
        portletManager = getUtility(IPortletManager, name=manager)
        assignable = getMultiAdapter((self.context, portletManager,), ILocalPortletAssignmentManager)
        
        def int2status(status):
            if status == 0:
                return None
            elif status > 0:
                return True
            else:
                return False
        
        assignable.setBlacklistStatus(USER_CATEGORY, int2status(user_status))
        assignable.setBlacklistStatus(GROUP_CATEGORY, int2status(group_status))
        assignable.setBlacklistStatus(CONTENT_TYPE_CATEGORY, int2status(content_type_status))
        assignable.setBlacklistStatus(CONTEXT_CATEGORY, int2status(context_status))
        
        baseUrl = str(getMultiAdapter((self.context, self.request), name='absolute_url'))
        self.request.response.redirect(baseUrl + '/@@manage-portlets')
        return ''
    
    # view @@convert-legacy-portlets
    
    def convert_legacy_portlets(self):
        
        portletsMapping = { 'portlet_login' : LoginPortletAssignment() }
        
        # Convert left_slots and right_slots to portlets
        
        left = getUtility(IPortletManager, name='plone.leftcolumn')
        right = getUtility(IPortletManager, name='plone.rightcolumn')
        
        leftAssignable = getMultiAdapter((self.context, left), IPortletAssignmentMapping)
        rightAssignable = getMultiAdapter((self.context, right), IPortletAssignmentMapping)
        
        leftChooser = INameChooser(leftAssignable)
        rightChooser = INameChooser(rightAssignable)
        
        left_slots = getattr(aq_base(self.context), 'left_slots', [])
        right_slots = getattr(aq_base(self.context), 'right_slots', [])
                
        for item in left_slots:
            path = item.split('/')
            if len(path) == 4:
                newPortlet = portletsMapping.get(path[1], None)
                if newPortlet is None and path[0] in ('context', 'here',) and path[2] == 'macros':
                    newPortlet = ClassicPortletAssignment(path[1], path[3])
                if newPortlet is not None:
                    leftAssignable[leftChooser.chooseName(None, newPortlet)] = newPortlet
                    
        for item in right_slots:
            path = item.split('/')
            if len(path) == 4:
                newPortlet = portletsMapping.get(path[1], None)
                if newPortlet is None and path[0] in ('context', 'here',) and path[2] == 'macros':
                    newPortlet = ClassicPortletAssignment(path[1], path[3])
                if newPortlet is not None:
                    rightAssignable[rightChooser.chooseName(None, newPortlet)] = newPortlet
                    
        self.context.left_slots = []
        self.context.right_slots = []
                    
        self.context.request.response.redirect(self.context.absolute_url() + '/@@manage-portlets')

class ManageCurrentUserPortlets(BrowserView):
    implements(IManageCurrentUserPortletsView)
        
    # IManagePortletsView implementation
    
    def getAssignmentMappingUrl(self, manager):
        baseUrl = str(getMultiAdapter((self.context, self.request), name='absolute_url'))
        return '%s/++myportlets++%s' % (baseUrl, manager.__name__)

    def getAssignmentsForManager(self, manager):
        userId = self._getUserId()
        column = getUtility(IPortletManager, name=manager.__name__)
        category = column[USER_CATEGORY]
        mapping = category.get(userId, None)
        if mapping is None:
            mapping = category[userId] = PortletAssignmentMapping()
        return mapping.values()
    
    def _getUserId(self):
        membership = getToolByName(self.context, 'portal_membership', None)
        if membership.isAnonymousUser():
            raise Unauthorized, "Cannot get portlet assignments for anonymous through this view"
        
        member = membership.getAuthenticatedMember()
        try:
            memberId = member.getUserId()
        except AttributeError:
            memberId = member.getId()
        
        if memberId is None:
            raise KeyError, "Cannot find user id of current user" 
        
        return memberId