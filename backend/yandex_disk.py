"""
Модуль для работы с Яндекс.Диском API
"""
import requests
from datetime import datetime, timedelta
from flask import current_app


class YandexDiskAPI:
    """Класс для работы с REST API Яндекс.Диска"""
    
    BASE_URL = 'https://cloud-api.yandex.net/v1/disk'
    OAUTH_URL = 'https://oauth.yandex.ru'
    APP_FOLDER = 'app:/FocusFlow'  # Папка приложения на диске
    
    def __init__(self, access_token):
        self.access_token = access_token
        self.headers = {
            'Authorization': f'OAuth {access_token}',
            'Content-Type': 'application/json'
        }
    
    @staticmethod
    def get_auth_url(client_id, redirect_uri):
        """Получить URL для авторизации пользователя"""
        return (
            f"{YandexDiskAPI.OAUTH_URL}/authorize?"
            f"response_type=code&"
            f"client_id={client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"scope=cloud_api:disk.app_folder cloud_api:disk.read cloud_api:disk.write cloud_api:disk.info"
        )
    
    @staticmethod
    def exchange_code_for_token(code, client_id, client_secret):
        """Обменять код авторизации на токен"""
        response = requests.post(
            f"{YandexDiskAPI.OAUTH_URL}/token",
            data={
                'grant_type': 'authorization_code',
                'code': code,
                'client_id': client_id,
                'client_secret': client_secret
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            expires_at = None
            if 'expires_in' in data:
                expires_at = datetime.utcnow() + timedelta(seconds=data['expires_in'])
            return {
                'access_token': data.get('access_token'),
                'refresh_token': data.get('refresh_token'),
                'expires_at': expires_at
            }
        return None
    
    @staticmethod
    def refresh_access_token(refresh_token, client_id, client_secret):
        """Обновить access_token используя refresh_token"""
        response = requests.post(
            f"{YandexDiskAPI.OAUTH_URL}/token",
            data={
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': client_id,
                'client_secret': client_secret
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            expires_at = None
            if 'expires_in' in data:
                expires_at = datetime.utcnow() + timedelta(seconds=data['expires_in'])
            return {
                'access_token': data.get('access_token'),
                'refresh_token': data.get('refresh_token', refresh_token),
                'expires_at': expires_at
            }
        return None
    
    def get_disk_info(self):
        """Получить информацию о диске"""
        try:
            response = requests.get(f"{self.BASE_URL}/", headers=self.headers)
            print(f"[YandexDisk API] get_disk_info status: {response.status_code}")
            if response.status_code == 200:
                return response.json()
            print(f"[YandexDisk API] Error response: {response.text}")
        except Exception as e:
            print(f"[YandexDisk API] Exception: {e}")
        return None
    
    def create_folder(self, path):
        """Создать папку на диске"""
        response = requests.put(
            f"{self.BASE_URL}/resources",
            headers=self.headers,
            params={'path': path}
        )
        return response.status_code in [201, 409]  # 409 = уже существует
    
    def ensure_app_folder(self):
        """Убедиться что папка приложения существует"""
        # Создаём основную папку
        self.create_folder(self.APP_FOLDER)
        # Создаём подпапки для разных типов файлов
        folders = ['music', 'image', 'document', 'video', 'archive', 'other']
        for folder in folders:
            self.create_folder(f"{self.APP_FOLDER}/{folder}")
        return True
    
    def get_upload_url(self, path, overwrite=False):
        """Получить URL для загрузки файла"""
        try:
            print(f"[YandexDisk API] Requesting upload URL for path: {path}")
            response = requests.get(
                f"{self.BASE_URL}/resources/upload",
                headers=self.headers,
                params={'path': path, 'overwrite': str(overwrite).lower()}
            )
            print(f"[YandexDisk API] get_upload_url status: {response.status_code}")
            
            if response.status_code == 200:
                href = response.json().get('href')
                print(f"[YandexDisk API] Upload URL obtained successfully")
                return href
            else:
                print(f"[YandexDisk API] get_upload_url error: {response.text}")
            return None
        except Exception as e:
            print(f"[YandexDisk API] get_upload_url exception: {e}")
            return None
    
    def upload_file(self, local_path, cloud_path, overwrite=False):
        """Загрузить файл на диск"""
        try:
            print(f"[YandexDisk API] Getting upload URL for: {cloud_path}")
            upload_url = self.get_upload_url(cloud_path, overwrite)
            
            if not upload_url:
                print(f"[YandexDisk API] Failed to get upload URL")
                return False
            
            print(f"[YandexDisk API] Upload URL obtained: {upload_url[:50]}...")
            
            with open(local_path, 'rb') as f:
                response = requests.put(upload_url, data=f)
            
            print(f"[YandexDisk API] Upload response status: {response.status_code}")
            
            if response.status_code not in [201, 202]:
                print(f"[YandexDisk API] Upload failed: {response.text}")
                return False
            
            return True
        except Exception as e:
            print(f"[YandexDisk API] Upload exception: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def upload_file_from_bytes(self, file_bytes, cloud_path, overwrite=False):
        """Загрузить файл из байтов"""
        upload_url = self.get_upload_url(cloud_path, overwrite)
        if not upload_url:
            return False
        
        response = requests.put(upload_url, data=file_bytes)
        return response.status_code in [201, 202]
    
    def get_download_url(self, path):
        """Получить URL для скачивания файла"""
        response = requests.get(
            f"{self.BASE_URL}/resources/download",
            headers=self.headers,
            params={'path': path}
        )
        if response.status_code == 200:
            return response.json().get('href')
        return None
    
    def get_public_url(self, path):
        """Опубликовать файл и получить публичную ссылку"""
        # Сначала публикуем
        response = requests.put(
            f"{self.BASE_URL}/resources/publish",
            headers=self.headers,
            params={'path': path}
        )
        
        if response.status_code == 200:
            # Получаем информацию о ресурсе с публичной ссылкой
            info = self.get_resource_info(path)
            if info and 'public_url' in info:
                return info['public_url']
        return None
    
    def get_resource_info(self, path):
        """Получить информацию о файле/папке"""
        response = requests.get(
            f"{self.BASE_URL}/resources",
            headers=self.headers,
            params={'path': path}
        )
        if response.status_code == 200:
            return response.json()
        return None
    
    def delete_resource(self, path, permanently=False):
        """Удалить файл или папку"""
        response = requests.delete(
            f"{self.BASE_URL}/resources",
            headers=self.headers,
            params={'path': path, 'permanently': str(permanently).lower()}
        )
        return response.status_code in [202, 204]
    
    def list_files(self, path, limit=100):
        """Получить список файлов в папке"""
        response = requests.get(
            f"{self.BASE_URL}/resources",
            headers=self.headers,
            params={'path': path, 'limit': limit}
        )
        if response.status_code == 200:
            data = response.json()
            if '_embedded' in data and 'items' in data['_embedded']:
                return data['_embedded']['items']
        return []
    
    def get_music_files(self):
        """Получить список музыкальных файлов"""
        return self.list_files(f"{self.APP_FOLDER}/music")
