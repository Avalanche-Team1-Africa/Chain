from django.contrib import admin
from .models import (
    CaseCategory,
    Case,
    CaseDocument,
    CaseUpdate,
    CaseMilestone,
    LawyerApplication,
)

# Optional: Customize the display of CaseCategory in the admin panel
class CaseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

# Optional: Customize the display of Case in the admin panel
class CaseAdmin(admin.ModelAdmin):
    list_display = ('title', 'ngo', 'category', 'urgency', 'status', 'created_at')
    list_filter = ('status', 'urgency', 'category', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')

    # Optional: Add a method to display total donations directly in the admin
    def total_donations(self, obj):
        return obj.total_donations()
    total_donations.short_description = 'Total Donations'

    # Include the total_donations method in the list display
    list_display += ('total_donations',)

# Optional: Customize the display of CaseDocument in the admin panel
class CaseDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'case', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('title', 'case__title')

# Optional: Customize the display of CaseUpdate in the admin panel
class CaseUpdateAdmin(admin.ModelAdmin):
    list_display = ('case', 'created_by', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('content', 'case__title')

# Optional: Customize the display of CaseMilestone in the admin panel
class CaseMilestoneAdmin(admin.ModelAdmin):
    list_display = ('case', 'title', 'target_date', 'status')
    list_filter = ('status', 'target_date')
    search_fields = ('title', 'case__title')

# Optional: Customize the display of LawyerApplication in the admin panel
class LawyerApplicationAdmin(admin.ModelAdmin):
    list_display = ('lawyer', 'case', 'status', 'applied_at')
    list_filter = ('status', 'applied_at')
    search_fields = ('lawyer__user__get_full_name', 'case__title')

# Register the models with their respective ModelAdmin classes (if customized)
admin.site.register(CaseCategory, CaseCategoryAdmin)
admin.site.register(Case, CaseAdmin)
admin.site.register(CaseDocument, CaseDocumentAdmin)
admin.site.register(CaseUpdate, CaseUpdateAdmin)
admin.site.register(CaseMilestone, CaseMilestoneAdmin)
admin.site.register(LawyerApplication, LawyerApplicationAdmin)