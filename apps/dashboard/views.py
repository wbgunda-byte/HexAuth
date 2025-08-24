"""
Dashboard views for HexAUTH system.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import (
    TemplateView, ListView, DetailView, CreateView, 
    UpdateView, DeleteView
)
from django.urls import reverse_lazy
from django.db.models import Q, Count
from django.utils import timezone
from django.core.paginator import Paginator

from apps.applications.models import Application
from apps.licenses.models import License
from apps.users.models import ApplicationUser
from apps.subscriptions.models import Subscription, UserSubscription
from apps.sessions.models import ApplicationSession
from apps.audit.models import AuditLog
from .forms import *


class DashboardMixin(LoginRequiredMixin):
    """
    Mixin for dashboard views with common functionality.
    """
    login_url = '/auth/login/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        
        # Get current application if set
        current_app_id = self.request.session.get('current_application_id')
        if current_app_id:
            try:
                context['current_application'] = Application.objects.get(
                    id=current_app_id,
                    owner=self.request.user
                )
            except Application.DoesNotExist:
                pass
        
        return context


class DashboardView(DashboardMixin, TemplateView):
    """
    Main dashboard view.
    """
    template_name = 'dashboard/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get user's applications
        applications = Application.objects.filter(owner=self.request.user)
        context['applications'] = applications
        
        # If user has only one app, auto-select it
        if applications.count() == 1 and not self.request.session.get('current_application_id'):
            app = applications.first()
            self.request.session['current_application_id'] = str(app.id)
            context['current_application'] = app
        
        # Dashboard stats
        if hasattr(context, 'current_application'):
            app = context['current_application']
            context['stats'] = {
                'total_licenses': app.licenses.count(),
                'used_licenses': app.licenses.filter(status=License.Status.USED).count(),
                'total_users': app.app_users.count(),
                'active_sessions': app.sessions.filter(
                    is_validated=True,
                    expires_at__gt=timezone.now()
                ).count(),
            }
        
        return context


class ApplicationListView(DashboardMixin, ListView):
    """
    List user's applications.
    """
    template_name = 'dashboard/applications/list.html'
    context_object_name = 'applications'
    paginate_by = 20
    
    def get_queryset(self):
        return Application.objects.filter(owner=self.request.user).order_by('-created_at')


class ApplicationDetailView(DashboardMixin, DetailView):
    """
    Application detail view.
    """
    template_name = 'dashboard/applications/detail.html'
    context_object_name = 'application'
    
    def get_queryset(self):
        return Application.objects.filter(owner=self.request.user)
    
    def get(self, request, *args, **kwargs):
        """Set current application in session."""
        self.object = self.get_object()
        request.session['current_application_id'] = str(self.object.id)
        return super().get(request, *args, **kwargs)


class LicenseListView(DashboardMixin, ListView):
    """
    List licenses for current application.
    """
    template_name = 'dashboard/licenses/list.html'
    context_object_name = 'licenses'
    paginate_by = 50
    
    def get_queryset(self):
        app_id = self.request.session.get('current_application_id')
        if not app_id:
            return License.objects.none()
        
        return License.objects.filter(
            application_id=app_id,
            application__owner=self.request.user
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add filter form
        context['filter_form'] = LicenseFilterForm(self.request.GET)
        
        # Add statistics
        queryset = self.get_queryset()
        context['license_stats'] = {
            'total': queryset.count(),
            'not_used': queryset.filter(status=License.Status.NOT_USED).count(),
            'used': queryset.filter(status=License.Status.USED).count(),
            'banned': queryset.filter(status=License.Status.BANNED).count(),
        }
        
        return context


class ApplicationUserListView(DashboardMixin, ListView):
    """
    List application users.
    """
    template_name = 'dashboard/users/list.html'
    context_object_name = 'users'
    paginate_by = 50
    
    def get_queryset(self):
        app_id = self.request.session.get('current_application_id')
        if not app_id:
            return ApplicationUser.objects.none()
        
        return ApplicationUser.objects.filter(
            application_id=app_id,
            application__owner=self.request.user
        ).order_by('-created_at')


class AccountSettingsView(DashboardMixin, UpdateView):
    """
    User account settings.
    """
    template_name = 'dashboard/account/settings.html'
    form_class = AccountSettingsForm
    success_url = reverse_lazy('dashboard:account_settings')
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'Account settings updated successfully!')
        return super().form_valid(form)