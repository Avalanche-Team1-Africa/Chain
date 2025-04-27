import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from .models import ChatMessage
from cases.models import Case

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        query_string = self.scope['query_string'].decode()
        token = None
        for param in query_string.split('&'):
            if param.startswith('token='):
                token = param.split('=')[1]
                break

        if not token:
            await self.close()
            return

        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            self.user = await database_sync_to_async(User.objects.get)(id=user_id)
        except Exception:
            await self.close()
            return

        self.case_id = self.scope['url_route']['kwargs']['case_id']
        self.room_group_name = f'chat_{self.case_id}'

        case = await database_sync_to_async(Case.objects.get)(pk=self.case_id)
        is_ngo = (self.user == case.ngo)
        is_lawyer = (
            self.user.role == 'LAWYER' and
            hasattr(self.user, 'lawyer_profile') and
            case.assigned_lawyer and
            self.user.lawyer_profile == case.assigned_lawyer
        )

        if not (is_ngo or is_lawyer):
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        chat_message = await database_sync_to_async(ChatMessage.objects.create)(
            case_id=self.case_id,
            sender=self.user,
            message=message
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': self.user.email,
                'timestamp': chat_message.timestamp.isoformat()
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
            'timestamp': event['timestamp']
        }))

class VideoCallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        query_string = self.scope['query_string'].decode()
        token = None
        for param in query_string.split('&'):
            if param.startswith('token='):
                token = param.split('=')[1]
                break

        if not token:
            await self.close()
            return

        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            self.user = await database_sync_to_async(User.objects.get)(id=user_id)
        except Exception:
            await self.close()
            return

        self.case_id = self.scope['url_route']['kwargs']['case_id']
        self.room_group_name = f'video_{self.case_id}'

        case = await database_sync_to_async(Case.objects.get)(pk=self.case_id)
        is_ngo = (self.user == case.ngo)
        is_lawyer = (
            self.user.role == 'LAWYER' and
            hasattr(self.user, 'lawyer_profile') and
            case.assigned_lawyer and
            self.user.lawyer_profile == case.assigned_lawyer
        )

        if not (is_ngo or is_lawyer):
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'video_message',
                'message': text_data_json
            }
        )

    async def video_message(self, event):
        await self.send(text_data=json.dumps(event['message']))