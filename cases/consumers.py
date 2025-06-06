import json
from channels.generic.websocket import AsyncWebsocketConsumer
from transformers import pipeline
from django.contrib.auth.models import User
from .models import ChatMessage, Case
from django.utils import timezone

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return
        
        self.room_group_name = f'chat_{self.user.id}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        case_id = text_data_json.get('case_id')

        # Save user message
        case = Case.objects.filter(id=case_id).first() if case_id else None
        chat_message = ChatMessage(
            user=self.user,
            case=case,
            message=message,
            is_user_message=True,
            timestamp=timezone.now()
        )
        chat_message.save()

        # Generate AI response
        nlp = pipeline('text-generation', model='distilgpt2')  # Replace with Grok if available
        context = (
            f"You are a support bot for a legal case management platform. "
            f"Provide helpful, concise responses to user queries about case management, document uploads, lawyer applications, and platform features. "
            f"User role: {self.user.role}. "
            f"Case: {case.title if case else 'None'}. "
            f"Query: {message}"
        )
        response = nlp(context, max_length=150, num_return_sequences=1)[0]['generated_text']
        response = response.replace(context, '').strip()

        # Save AI response
        ai_message = ChatMessage(
            user=self.user,
            case=case,
            message=response,
            is_user_message=False,
            timestamp=timezone.now()
        )
        ai_message.save()

        # Send response to client
        await self.send(text_data=json.dumps({
            'message': response,
            'sender': 'bot',
            'timestamp': ai_message.timestamp.isoformat(),
            'case_id': case_id
        }))