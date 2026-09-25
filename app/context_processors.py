def admin_context(request):
    """
    Injects 'is_admin' into all templates so the navbar and 
    other components know if an admin is logged in.
    """
    return {
        'is_admin': request.session.get('is_admin', False)
    }
