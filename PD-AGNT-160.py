import json
import os

from dotenv import load_dotenv
import requests


class IpDetector:
    def __init__(self):
        self.base_url = "https://ifconfig.me"

    def get_current_ip(self):
        try:
            response = requests.get(self.base_url, timeout=10)
        except requests.RequestException as e:
            print(f"Ошибка сети при запросе к ifconfig.me: {e}")
            return None

        if response.status_code == 200:
            return response.text.strip()

        print(f"Ошибка в запросе к ifconfig.me! Статус: {response.status_code}")
        return None


class IpInfoProvider:
    def __init__(self):
        self.base_url = "https://ipinfo.io"

    def get_location_info(self, ip_address):
        full_url = f"{self.base_url}/{ip_address}/geo"

        try:
            response = requests.get(full_url, timeout=10)
        except requests.RequestException as e:
            print(f"Ошибка сети при запросе к IpInfo: {e}")
            return None

        if response.status_code == 200:
            return response.json()

        print(f"Ошибка в запросе к IpInfo! Статус: {response.status_code}")
        return None


class YandexDiskUploader:
    def __init__(self, token):
        self.token = token
        self.base_url = "https://cloud-api.yandex.net/v1/disk/resources"
        self.headers = {
            "Authorization": f"OAuth {self.token}"
        }

    def create_folder(self, folder_name):
        params = {"path": f"disk:/{folder_name}"}

        try:
            response = requests.put(
                self.base_url, headers=self.headers, params=params, timeout=10
            )
        except requests.RequestException as e:
            print(f"Ошибка сети при создании папки: {e}")
            return False

        if response.status_code == 201:
            print(f"Папка '{folder_name}' успешно создана на Яндекс.Диске!")
            return True
        elif response.status_code == 409:
            print(f"Папка '{folder_name}' уже существует, пересоздание не требуется.")
            return True
        else:
            print(f"Не удалось создать папку. Статус-код: {response.status_code}")
            return False

    def upload_file(self, folder_name, local_file_path):
        upload_endpoint = f"{self.base_url}/upload"
        params = {
            "path": f"disk:/{folder_name}/{local_file_path}",
            "overwrite": "true"
        }

        try:
            response = requests.get(
                upload_endpoint, headers=self.headers, params=params, timeout=10
            )
        except requests.RequestException as e:
            print(f"Ошибка сети при получении ссылки на загрузку: {e}")
            return False

        if response.status_code != 200:
            print(f"Не удалось получить ссылку на загрузку. Статус-код: {response.status_code}")
            return False

        secret_upload_url = response.json().get("href")

        try:
            with open(local_file_path, "rb") as file_bytes:
                put_response = requests.put(secret_upload_url, data=file_bytes, timeout=30)
        except requests.RequestException as e:
            print(f"Ошибка сети при загрузке файла: {e}")
            return False
        except OSError as e:
            print(f"Ошибка чтения файла: {e}")
            return False

        if put_response.status_code == 201:
            print(f"Файл '{local_file_path}' успешно загружен в папку '{folder_name}'!")
            return True

        print(f"Ошибка загрузки файла. Статус: {put_response.status_code}")
        return False


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, ".env")
    load_dotenv(env_path)

    YANDEX_TOKEN = os.getenv("YANDEX_TOKEN", "")
    print(f"Системный лог: Считано символов токена — {len(YANDEX_TOKEN)}")

    if not YANDEX_TOKEN:
        print("Токен Яндекс.Диска не найден. Проверьте файл .env")
        return

    detector = IpDetector()
    my_ip = detector.get_current_ip()
    print(f"My IP address: {my_ip}")

    if not my_ip:
        print("Не удалось определить IP. Выход.")
        return

    info_provider = IpInfoProvider()
    geo_data = info_provider.get_location_info(my_ip)
    print(f"My GEO data: {geo_data}")

    if not geo_data or "city" not in geo_data:
        print("Не удалось получить город из гео-данных. Выход.")
        return

    clean_data = {my_ip: geo_data["city"]}

    with open("visit_info.json", "w", encoding="utf-8") as file:
        json.dump(clean_data, file, ensure_ascii=False, indent=4)
    print("Файл visit_info.json успешно создан!")

    uploader = YandexDiskUploader(YANDEX_TOKEN)
    uploader.create_folder("IpDetector")
    upload_success = uploader.upload_file("IpDetector", "visit_info.json")

    if upload_success and os.path.exists("visit_info.json"):
        os.remove("visit_info.json")
        print("Локальный файл visit_info.json успешно удален.")


if __name__ == "__main__":
    main()