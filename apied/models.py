# apied/models.py

import uuid
from django.db import models
from django.contrib.auth.models import User

# Define available project types (Categories)
PROJECT_TYPE_CHOICES = [
    ('frontend', 'Frontend Development'),
    ('backend', 'Backend Development'),
    ('fullstack', 'Full-Stack Application'),
    ('mobile', 'Mobile Application'),
    ('design', 'UI/UX Design'),
    ('other', 'Other'),
]

class ProjectPost(models.Model):
    """
    Model to store public project links, descriptions, and media.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects', help_text="The user who posted this project.")
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    project_url = models.URLField(max_length=500, verbose_name="Demo/Primary Link")
    project_type = models.CharField(max_length=20, choices=PROJECT_TYPE_CHOICES, default='fullstack', verbose_name="Category")
    
    # Image Upload/Link Fields
    screenshot = models.ImageField(upload_to='project_screenshots/', blank=True, null=True, help_text="Upload a screenshot of the project.")
    screenshot_url_fallback = models.URLField(max_length=500, blank=True, null=True, verbose_name="Fallback Image Link", help_text="A direct URL to a public image if no file is uploaded.")
    
    # --- NEW: Additional Optional Fields ---
    source_code_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="Source Code Link", help_text="Link to the GitHub repository or source code download.")
    custom_field_name = models.CharField(max_length=50, blank=True, null=True, verbose_name="Custom Field Label", help_text="Optional: A label for an extra piece of information (e.g., 'Tech Stack').")
    custom_field_value = models.TextField(blank=True, null=True, verbose_name="Custom Field Content", help_text="Optional: The content for your custom field (e.g., 'Django, React, PostgreSQL').")
    
    is_public = models.BooleanField(default=True, verbose_name="Publicly Visible", help_text="If unchecked, only you can see it on your portfolio.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Project Post"
        verbose_name_plural = "Project Posts"

    def __str__(self):
        return f"{self.title} by {self.user.username}"
    
    def get_screenshot_url(self, request=None):
        """
        Returns the absolute uploaded image URL or the fallback URL.
        The 'request' object is needed to build the full URL.
        """
        if self.screenshot and hasattr(self.screenshot, 'url'):
            if request:
                return request.build_absolute_uri(self.screenshot.url)
            return self.screenshot.url
        return self.screenshot_url_fallback


class ProjectResource(models.Model):
    """
    Model for supplementary links (e.g., documentation, second demo).
    """
    project = models.ForeignKey(ProjectPost, on_delete=models.CASCADE, related_name='resources')
    name = models.CharField(max_length=100)
    resource_url = models.URLField(max_length=500, verbose_name="Resource Link")

    def __str__(self):
        return f"{self.name} for {self.project.title}"


class Comment(models.Model):
    """
    Model for user comments on a project post.
    """
    project = models.ForeignKey(ProjectPost, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.user.username} on {self.project.title}"


class Like(models.Model):
    """
    Model for user likes on a project post. A user can only like a post once.
    """
    project = models.ForeignKey(ProjectPost, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('project', 'user') # Enforces one like per user per project
        verbose_name = "Like"
        verbose_name_plural = "Likes"

    def __str__(self):
        return f"Like by {self.user.username} on {self.project.title}"

# --- NEW: Service Request Models ---

def generate_request_code():
    """Generates a unique 8-character alphanumeric code."""
    return uuid.uuid4().hex[:8].upper()

class ServiceRequest(models.Model):
    """Model for client service requests."""
    SERVICE_CHOICES = [
        ('build_idea', 'Build Your Idea'),
        ('build_website', 'Build a Website'),
        ('build_software', 'Build Software'),
        ('cybersecurity', 'Cybersecurity Services'),
        ('training', 'Training'),
        ('team_management', 'Team Management'),
        ('join_us', 'Join Us'),
        ('other', 'Other'),
    ]
    ORGANIZATION_TYPE_CHOICES = [
        ('company', 'Company/Organization'),
        ('individual', 'Individual'),
    ]
    BUDGET_CHOICES = [
        ('below_20k', 'Below 20,000 RWF'),
        ('20k_50k', '20,000 - 50,000 RWF'),
        ('50k_100k', '50,000 - 100,000 RWF'),
        ('100k_200k', '100,000 - 200,000 RWF'),
        ('200k_500k', '200,000 - 500,000 RWF'),
        ('above_500k', 'Above 500,000 RWF'),
    ]
    
    # Unique code for tracking
    request_code = models.CharField(max_length=8, default=generate_request_code, unique=True, editable=False)
    
    # User linkage (optional)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='service_requests')

    # Step 1: Service & Location
    service_type = models.CharField(max_length=50, choices=SERVICE_CHOICES)
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    organization_type = models.CharField(max_length=20, choices=ORGANIZATION_TYPE_CHOICES)
    organization_name = models.CharField(max_length=255, help_text="Your company or your full name")
    preferred_language = models.CharField(max_length=50)

    # Step 2: Job Details
    job_category = models.CharField(max_length=100, blank=True, help_text="e.g., E-commerce, Portfolio, ERP System")
    job_description = models.TextField()
    job_attachment_url = models.URLField(max_length=500, blank=True, null=True, help_text="Link to a document or image (e.g., Google Drive, Dropbox)")
    due_date = models.DateField(null=True, blank=True)
    
    # Step 3: Contact & Budget
    primary_phone = models.CharField(max_length=20)
    secondary_phone = models.CharField(max_length=20, blank=True)
    primary_email = models.EmailField()
    budget_range = models.CharField(max_length=20, choices=BUDGET_CHOICES)
    terms_accepted = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Service Request"
        verbose_name_plural = "Service Requests"

    def __str__(self):
        return f"Request {self.request_code} from {self.organization_name}"

class AdminReview(models.Model):
    """Model for admin feedback on a service request."""
    service_request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name='reviews')
    admin_user = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'is_staff': True})
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review by {self.admin_user.username} on {self.service_request.request_code}"

# --- NEW: Tariff/Pricing Model ---
class Tariff(models.Model):
    """
    Model for dynamic services and prices (tariffs).
    """
    title = models.CharField(max_length=100, help_text="The name of the service or package.")
    description = models.TextField(blank=True, help_text="A short explanation of what the service includes.")
    price = models.CharField(max_length=50, help_text="The price, e.g., '150,000 RWF' or 'Contact Us'.")
    redirect_url = models.URLField(max_length=500, help_text="The URL to redirect to when this tariff is clicked.")
    color = models.CharField(max_length=7, default='#6366F1', help_text="Hex color code for the tariff display (e.g., #6366F1).")
    order = models.PositiveIntegerField(default=0, help_text="Display order (lower numbers show up first).")
    is_active = models.BooleanField(default=True, help_text="Uncheck this to hide the tariff from the public view.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = "Tariff"
        verbose_name_plural = "Tariffs"

    def __str__(self):
        return f"{self.title} - {self.price}"
