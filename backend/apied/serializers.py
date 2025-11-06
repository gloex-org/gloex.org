# apied/serializers.py

from rest_framework import serializers
from .models import JobRequest
from django.contrib.auth.models import User

# --- JobRequest Serializer ---

class JobRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for the JobRequest model. 
    Used for creation (POST) and detailed view (GET/PATCH).
    """
    # Read-only fields for the client
    request_code = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    service_type_display = serializers.CharField(source='get_service_type_display', read_only=True)
    organization_type_display = serializers.CharField(source='get_organization_type_display', read_only=True)
    budget_range_display = serializers.CharField(source='get_budget_range_display', read_only=True)
    
    # Display the username if a registered user submitted it
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = JobRequest
        fields = '__all__'
        # Fields that clients should not be allowed to modify via the general public API
        read_only_fields = ('user', 'status', 'admin_review_note') 
        
# --- Admin/Staff JobRequest List Serializer (Minimal View) ---
class JobRequestAdminListSerializer(serializers.ModelSerializer):
    """
    Minimal serializer for admin listing view.
    """
    username = serializers.CharField(source='user.username', read_only=True)
    is_registered = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = JobRequest
        fields = ('id', 'request_code', 'service_type', 'status', 'created_at', 'contact_email_1', 'contact_phone_1', 'username', 'is_registered', 'status_display')

    def get_is_registered(self, obj):
        return obj.user is not None

# --- Minimal Serializer for Client to Comment/Update an existing request ---
class JobRequestClientUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer used specifically for client to update their request details.
    Clients can update the description and file link, which acts as their way to 'comment' 
    or submit new information for the admin to review.
    """
    
    class Meta:
        model = JobRequest
        fields = ('job_description', 'file_fallback_link', 'execution_how', 'reason_why') 
        
# --- Admin Update Serializer ---
class JobRequestAdminUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for Admin to update status and add notes.
    """
    class Meta:
        model = JobRequest
        fields = ('status', 'admin_review_note')
