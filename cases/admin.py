from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import (
    Case, CaseMilestone, CaseEvent, CaseMessage,
    CaseMessageAttachment, CaseDocument, DocumentTemplate,
)


class CaseMilestoneInline(admin.TabularInline):
    """Inline admin for CaseMilestone."""
    model = CaseMilestone
    extra = 0


class CaseEventInline(admin.TabularInline):
    """Inline admin for CaseEvent."""
    model = CaseEvent
    extra = 0


class CaseDocumentInline(admin.TabularInline):
    """Inline admin for CaseDocument."""
    model = CaseDocument
    extra = 0


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    """Admin for the Case model."""
    # Removed 'reference_number' which isn't a field on Case model
    list_display = ('id', 'title', 'ngo', 'assigned_lawyer', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'description')  # Removed 'reference_number'
    inlines = [CaseMilestoneInline, CaseEventInline, CaseDocumentInline]
    date_hierarchy = 'created_at'


class CaseMessageAttachmentInline(admin.TabularInline):
    """Inline admin for CaseMessageAttachment."""
    model = CaseMessageAttachment
    extra = 0


@admin.register(CaseMessage)
class CaseMessageAdmin(admin.ModelAdmin):
    """Admin for the CaseMessage model."""
    list_display = ('sender', 'case', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('content',)
    inlines = [CaseMessageAttachmentInline]
    date_hierarchy = 'timestamp'


@admin.register(CaseEvent)
class CaseEventAdmin(admin.ModelAdmin):
    """Admin for the CaseEvent model."""
    list_display = ('title', 'case', 'event_type', 'start_time', 'end_time', 'created_by')
    list_filter = ('event_type', 'start_time')
    search_fields = ('title', 'description')
    date_hierarchy = 'start_time'


@admin.register(CaseDocument)
class CaseDocumentAdmin(admin.ModelAdmin):
    """Admin for the CaseDocument model."""
    # Removed 'document_type' and 'uploaded_by' which aren't fields on CaseDocument
    list_display = ('name', 'case', 'uploaded_at')
    list_filter = ('uploaded_at',)  # Removed 'document_type'
    search_fields = ('name', 'notes')
    date_hierarchy = 'uploaded_at'


@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    """Admin for the DocumentTemplate model."""
    list_display = ('name', 'available_to_ngo', 'available_to_lawyer', 'created_at')
    list_filter = ('available_to_ngo', 'available_to_lawyer', 'created_at')
    search_fields = ('name', 'description')


    


# Register remaining models if needed
admin.site.register(CaseMilestone)
admin.site.register(CaseMessageAttachment)