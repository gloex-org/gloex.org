# apied/views.py

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q # Added Q for search queries
import json
from .models import ProjectPost, ProjectResource, Comment, Like, ServiceRequest, AdminReview, Tariff

# --- Helper Serializer Functions ---

def serialize_user(user):
    """Returns essential user data."""
    if not user.is_authenticated:
        return {'is_authenticated': False}
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_authenticated': True,
    }

def serialize_resource(resource):
    """Returns project resource data."""
    return {
        'id': resource.id,
        'name': resource.name,
        'resource_url': resource.resource_url,
    }

def serialize_comment(comment):
    """Returns comment data."""
    return {
        'id': comment.id,
        'content': comment.content,
        'username': comment.user.username,
        'user_id': comment.user.id,
        'created_at': comment.created_at.isoformat(),
    }

def serialize_project(project, request=None, include_details=False):
    """
    Returns project post data, with optional details for the full view.
    The 'request' object is crucial for building absolute URLs for media.
    """
    data = {
        'id': project.id,
        'title': project.title,
        'description': project.description,
        'project_url': project.project_url,
        'project_type': project.get_project_type_display(),
        'screenshot_url': project.get_screenshot_url(request), # Pass request to get absolute URL
        'is_public': project.is_public,
        'created_at': project.created_at.isoformat(),
        'username': project.user.username,
        'user_id': project.user.id,
        'likes_count': project.likes.count(),
        # --- NEW: Serialize additional fields ---
        'source_code_url': project.source_code_url,
        'custom_field_name': project.custom_field_name,
        'custom_field_value': project.custom_field_value,
    }

    if include_details:
        data['resources'] = [serialize_resource(r) for r in project.resources.all()]
        data['comments'] = [serialize_comment(c) for c in project.comments.all().order_by('-created_at')]
    
    return data

# --- NEW: Service Request Serializers ---

def serialize_admin_review(review):
    """Returns admin review data."""
    return {
        'id': review.id,
        'admin_username': review.admin_user.username,
        'comment': review.comment,
        'created_at': review.created_at.isoformat(),
    }

def serialize_service_request(service_request):
    """Returns detailed service request data."""
    data = {
        'request_code': service_request.request_code,
        'service_type': service_request.get_service_type_display(),
        'country': service_request.country,
        'city': service_request.city,
        'organization_type': service_request.get_organization_type_display(),
        'organization_name': service_request.organization_name,
        'preferred_language': service_request.preferred_language,
        'job_category': service_request.job_category,
        'job_description': service_request.job_description,
        'job_attachment_url': service_request.job_attachment_url,
        'due_date': service_request.due_date.isoformat() if service_request.due_date else None,
        'primary_phone': service_request.primary_phone,
        'secondary_phone': service_request.secondary_phone,
        'primary_email': service_request.primary_email,
        'budget_range': service_request.get_budget_range_display(),
        'created_at': service_request.created_at.isoformat(),
        'reviews': [serialize_admin_review(r) for r in service_request.reviews.all()]
    }
    if service_request.user:
        data['username'] = service_request.user.username
    return data

# --- NEW: Tariff Serializer ---
def serialize_tariff(tariff):
    """Returns tariff data."""
    return {
        'id': tariff.id,
        'title': tariff.title,
        'description': tariff.description,
        'price': tariff.price,
        'redirect_url': tariff.redirect_url,
        'color': tariff.color,
        'order': tariff.order,
    }


# --- Authentication Views (Unchanged) ---
@ensure_csrf_cookie
def current_user_view(request):
    return JsonResponse(serialize_user(request.user))

@csrf_exempt
def register_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests allowed'}, status=405)
    try:
        data = json.loads(request.body)
        username, password = data.get('username'), data.get('password')
        if not username or not password:
            return JsonResponse({'error': 'Username and password are required.'}, status=400)
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'This username is already taken.'}, status=409)
        user = User.objects.create_user(username=username, password=password, email=data.get('email', ''))
        login(request, user)
        return JsonResponse(serialize_user(user), status=201)
    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {e}'}, status=500)

@csrf_exempt
def login_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests allowed'}, status=405)
    try:
        data = json.loads(request.body)
        user = authenticate(request, username=data.get('username'), password=data.get('password'))
        if user is not None:
            login(request, user)
            return JsonResponse(serialize_user(user))
        else:
            return JsonResponse({'error': 'Invalid credentials.'}, status=401)
    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {e}'}, status=500)

@login_required
@csrf_exempt
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return JsonResponse({'message': 'Successfully logged out.'})
    return JsonResponse({'error': 'Only POST requests allowed'}, status=405)


# --- Project Views (UPDATED) ---
@csrf_exempt
def projects_list_create_view(request):
    if request.method == 'GET':
        projects = ProjectPost.objects.filter(is_public=True).order_by('-created_at')
        data = [serialize_project(p, request) for p in projects]
        return JsonResponse(data, safe=False)

    elif request.method == 'POST':
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required.'}, status=403)
        
        try:
            project = ProjectPost.objects.create(
                user=request.user,
                title=request.POST.get('title'),
                description=request.POST.get('description', ''),
                project_url=request.POST.get('project_url'),
                project_type=request.POST.get('project_type', 'fullstack'),
                screenshot=request.FILES.get('screenshot'),
                screenshot_url_fallback=request.POST.get('screenshot_url_fallback', ''),
                is_public=request.POST.get('is_public') == 'on',
                # --- NEW: Handle new fields on creation ---
                source_code_url=request.POST.get('source_code_url', ''),
                custom_field_name=request.POST.get('custom_field_name', ''),
                custom_field_value=request.POST.get('custom_field_value', ''),
            )
            return JsonResponse(serialize_project(project, request), status=201)
        except Exception as e:
            return JsonResponse({'error': f'Project creation failed: {e}'}, status=500)
    
    return JsonResponse({'error': 'Method not allowed.'}, status=405)


@csrf_exempt
def project_detail_update_delete_view(request, pk):
    project = get_object_or_404(ProjectPost, pk=pk)
    
    if request.method == 'GET':
        # Check if user has access (is owner or project is public)
        if not project.is_public and project.user != request.user:
             return JsonResponse({'error': 'Project not found or you do not have permission.'}, status=404)
        data = serialize_project(project, request, include_details=True)
        data['user_has_liked'] = request.user.is_authenticated and project.likes.filter(user=request.user).exists()
        return JsonResponse(data)

    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required.'}, status=403)
    
    # --- UPDATED: Allow owner or staff to modify/delete ---
    if project.user != request.user and not request.user.is_staff:
        return JsonResponse({'error': 'You do not have permission to modify this project.'}, status=403)

    if request.method == 'DELETE':
        project.delete()
        return JsonResponse({'message': 'Project successfully deleted.'}, status=204)

    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            project.title = data.get('title', project.title)
            project.description = data.get('description', project.description)
            project.project_url = data.get('project_url', project.project_url)
            project.project_type = data.get('project_type', project.project_type)
            project.is_public = data.get('is_public', project.is_public)
            # --- NEW: Update additional fields ---
            project.source_code_url = data.get('source_code_url', project.source_code_url)
            project.custom_field_name = data.get('custom_field_name', project.custom_field_name)
            project.custom_field_value = data.get('custom_field_value', project.custom_field_value)
            project.save()
            return JsonResponse(serialize_project(project, request, include_details=True))
        except Exception as e:
            return JsonResponse({'error': f'Update failed: {e}'}, status=400)

    return JsonResponse({'error': 'Method not allowed.'}, status=405)


# --- Interaction Views (Like, Comment, etc.) ---
@csrf_exempt
@login_required
def like_toggle_view(request, pk):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)
    project = get_object_or_404(ProjectPost, pk=pk)
    like, created = Like.objects.get_or_create(project=project, user=request.user)
    action = 'liked' if created else 'unliked'
    if not created:
        like.delete()
    return JsonResponse({'action': action, 'likes_count': project.likes.count()})


@csrf_exempt
@login_required
def comment_list_create_view(request, pk):
    project = get_object_or_404(ProjectPost, pk=pk)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            content = data.get('content')
            if not content:
                return JsonResponse({'error': 'Comment content is required.'}, status=400)
            comment = Comment.objects.create(project=project, user=request.user, content=content)
            return JsonResponse(serialize_comment(comment), status=201)
        except Exception as e:
            return JsonResponse({'error': f'Failed to post comment: {e}'}, status=400)
    return JsonResponse({'error': 'Method not allowed.'}, status=405)


# --- NEW: View to delete a comment ---
@csrf_exempt
@login_required
def comment_delete_view(request, pk, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id, project__id=pk)
    
    # Allow deletion if user is comment owner, project owner, or staff
    if request.user == comment.user or request.user == comment.project.user or request.user.is_staff:
        if request.method == 'DELETE':
            comment.delete()
            return JsonResponse({'message': 'Comment deleted successfully.'}, status=204)
        return JsonResponse({'error': 'Only DELETE method allowed.'}, status=405)
    
    return JsonResponse({'error': 'You do not have permission to delete this comment.'}, status=403)


# --- NEW: View for project search ---
def project_search_view(request):
    query = request.GET.get('q', '')
    if not query:
        return JsonResponse([], safe=False)

    # Search in title, description, and username
    projects = ProjectPost.objects.filter(
        Q(is_public=True) & (
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(user__username__icontains=query)
        )
    ).order_by('-created_at')

    data = [serialize_project(p, request) for p in projects]
    return JsonResponse(data, safe=False)


# --- Portfolio and Resource Views (Largely Unchanged) ---
def user_portfolio_view(request, username):
    user = get_object_or_404(User, username=username)
    projects = user.projects.all().order_by('-created_at')
    # Filter for public projects if the viewer is not the owner
    if request.user != user:
        projects = projects.filter(is_public=True)
    data = [serialize_project(p, request) for p in projects]
    return JsonResponse(data, safe=False)

@csrf_exempt
@login_required
def resource_list_create_view(request, pk):
    # This view remains for adding supplementary resources like documentation.
    # The source code is now a dedicated field on the project itself.
    project = get_object_or_404(ProjectPost, pk=pk)
    if project.user != request.user and not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied.'}, status=403)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            resource = ProjectResource.objects.create(
                project=project,
                name=data.get('name'),
                resource_url=data.get('resource_url')
            )
            return JsonResponse(serialize_resource(resource), status=201)
        except Exception as e:
            return JsonResponse({'error': f'Failed to add resource: {e}'}, status=400)
    
    return JsonResponse([serialize_resource(r) for r in project.resources.all()], safe=False)


# --- NEW: Service Request Views ---

@csrf_exempt
def service_request_create_view(request):
    """Handles submission of the service request form."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        # Simple validation
        required_fields = ['service_type', 'country', 'city', 'organization_type', 'organization_name', 
                           'preferred_language', 'job_description', 'primary_phone', 'primary_email', 'budget_range', 'terms_accepted']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({'error': f'Missing required field: {field}'}, status=400)

        if not data.get('terms_accepted'):
            return JsonResponse({'error': 'You must accept the terms and conditions.'}, status=400)

        new_request = ServiceRequest.objects.create(
            user=request.user if request.user.is_authenticated else None,
            service_type=data.get('service_type'),
            country=data.get('country'),
            city=data.get('city'),
            organization_type=data.get('organization_type'),
            organization_name=data.get('organization_name'),
            preferred_language=data.get('preferred_language'),
            job_category=data.get('job_category', ''),
            job_description=data.get('job_description'),
            job_attachment_url=data.get('job_attachment_url'),
            due_date=data.get('due_date') or None,
            primary_phone=data.get('primary_phone'),
            secondary_phone=data.get('secondary_phone', ''),
            primary_email=data.get('primary_email'),
            budget_range=data.get('budget_range'),
            terms_accepted=data.get('terms_accepted'),
        )
        return JsonResponse({'message': 'Request submitted successfully.', 'request_code': new_request.request_code}, status=201)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'An unexpected error occurred: {e}'}, status=500)


@csrf_exempt
def service_request_detail_view(request):
    """Fetches a service request by its unique code."""
    code = request.GET.get('code', '').strip().upper()
    if not code:
        return JsonResponse({'error': 'A request code is required.'}, status=400)

    try:
        service_request = get_object_or_404(ServiceRequest, request_code=code)
        return JsonResponse(serialize_service_request(service_request))
    except ServiceRequest.DoesNotExist:
        return JsonResponse({'error': 'Invalid request code.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {e}'}, status=500)

# --- NEW: Tariff View ---
def tariff_list_view(request):
    """
    Provides a list of all active tariffs, ordered by the 'order' field.
    This view is public and does not require authentication.
    """
    if request.method == 'GET':
        tariffs = Tariff.objects.filter(is_active=True).order_by('order')
        data = [serialize_tariff(t) for t in tariffs]
        return JsonResponse(data, safe=False)
    
    return JsonResponse({'error': 'Only GET requests are allowed.'}, status=405)
