from django.contrib import admin
from .admin_config import get_category_for_model

class EduNestAdminSite(admin.AdminSite):
    site_header = 'EduNest Administration'
    site_title = 'EduNest Admin Portal'
    index_title = 'Welcome to EduNest ERP'

    def get_app_list(self, request, app_label=None):
        """
        Return a sorted list of apps (categories) and their models.
        """
        # Get the standard app list from the base class
        app_dict = self._build_app_dict(request, app_label)
        
        if not app_dict:
            return []

        # Create a new structure based on our categories
        custom_categories = {}
        
        for app_label_key, app_data in app_dict.items():
            for model in app_data['models']:
                # Determine category using our config
                category = get_category_for_model(model['object_name'])
                
                if category not in custom_categories:
                    custom_categories[category] = {
                        'name': category,
                        'app_label': category.lower(),
                        'app_url': f'#category-{category.lower()}',
                        'has_module_perms': True,
                        'models': [],
                    }
                
                custom_categories[category]['models'].append(model)

        # Sort models within each category
        for category in custom_categories.values():
            category['models'].sort(key=lambda x: x['name'])

        # Sort categories based on the order in ADMIN_GROUPS + 'Other'
        from .admin_config import ADMIN_GROUPS
        category_order = list(ADMIN_GROUPS.keys()) + ['Other']
        
        sorted_app_list = []
        for cat_name in category_order:
            if cat_name in custom_categories:
                sorted_app_list.append(custom_categories[cat_name])
        
        # Add any categories not in the order list
        for cat_name, cat_data in custom_categories.items():
            if cat_name not in category_order:
                sorted_app_list.append(cat_data)

        return sorted_app_list

# Instantiate the custom admin site
admin_site = EduNestAdminSite(name='edunest_admin')
