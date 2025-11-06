from django.contrib import admin
from .models import ProjectPost, ProjectResource, Comment, Like, ServiceRequest, AdminReview, Tariff

# Register your models here.
@admin.register(ProjectPost)
class ProjectPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'project_type', 'is_public', 'created_at')
    list_filter = ('project_type', 'is_public')
    search_fields = ('title', 'description', 'user__username')
    date_hierarchy = 'created_at'

@admin.register(ProjectResource)
class ProjectResourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'resource_url')
    search_fields = ('name', 'project__title')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'created_at', 'content')
    list_filter = ('project',)
    search_fields = ('user__username', 'content')

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'created_at')
    list_filter = ('project',)
    search_fields = ('user__username', 'project__title')

# --- NEW: Service Request Admin ---

class AdminReviewInline(admin.TabularInline):
    """Allows adding reviews directly within the service request view."""
    model = AdminReview
    extra = 1 # Show one empty review form
    readonly_fields = ('created_at',)
    
    def get_formset(self, request, obj=None, **kwargs):
        """Automatically set the admin user."""
        formset = super().get_formset(request, obj, **kwargs)
        formset.form.base_fields['admin_user'].initial = request.user
        return formset

@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ('request_code', 'organization_name', 'service_type', 'primary_email', 'created_at')
    list_filter = ('service_type', 'budget_range', 'organization_type', 'created_at')
    search_fields = ('request_code', 'organization_name', 'primary_email', 'job_description')
    readonly_fields = ('request_code', 'created_at', 'updated_at', 'user')
    inlines = [AdminReviewInline]
    
    fieldsets = (
        ('Request Details', {
            'fields': ('request_code', 'user', 'service_type', 'budget_range', 'terms_accepted')
        }),
        ('Client Information', {
            'fields': ('organization_name', 'organization_type', 'country', 'city', 'preferred_language')
        }),
        ('Contact Information', {
            'fields': ('primary_email', 'primary_phone', 'secondary_phone')
        }),
        ('Job Description', {
            'fields': ('job_category', 'job_description', 'job_attachment_url', 'due_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )

@admin.register(AdminReview)
class AdminReviewAdmin(admin.ModelAdmin):
    list_display = ('service_request', 'admin_user', 'created_at')
    search_fields = ('service_request__request_code', 'admin_user__username', 'comment')

# --- NEW: Tariff Admin ---
@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'order', 'is_active', 'redirect_url')
    list_filter = ('is_active',)
    search_fields = ('title', 'description', 'price')
    list_editable = ('order', 'is_active', 'price') # Allow quick edits from the list view
