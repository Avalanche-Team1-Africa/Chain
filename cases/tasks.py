from celery import shared_task
from transformers import pipeline

@shared_task
def generate_response(message, context, user_id, case_id):
    nlp = pipeline('text-generation', model='distilgpt2')
    response = nlp(context, max_length=150, num_return_sequences=1)[0]['generated_text']
    response = response.replace(context, '').strip()
    
    from .models import ChatMessage, Case
    from django.contrib.auth.models import User
    case = Case.objects.filter(id=case_id).first() if case_id else None
    ai_message = ChatMessage(
        user=User.objects.get(id=user_id),
        case=case,
        message=response,
        is_user_message=False,
    )
    ai_message.save()
    return response
