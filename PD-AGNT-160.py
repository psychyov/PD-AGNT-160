import json
import os

from dotenv import load_dotenv
import requests


class IpDetector:
    def __init__(self):
        self.base_url = "https://ifconfig.me"

    def get_current_ip(self):
        response = requests.get(self.base_url)

        if response.status_code == 200:
            return response.text.strip()
        else:
            print(f"Ошибка в запросе к ifconfig.me! Статус: {response.status_code}")
            return None


class IpInfoProvider:
    def __init__(self):
        self.base_url = "https://ipinfo.io"

    def get_location_info(self, ip_address):
        full_url = f"{self.base_url}/{ip_address}/geo"
        response = requests.get(full_url)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Ошибка в заспросе к IpInfo! Статус: {response.status_code}")
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
        response = requests.put(self.base_url, headers=self.headers, params=params)

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

        response = requests.get(upload_endpoint, headers=self.headers, params=params)

        if response.status_code == 200:
            secret_upload_url = response.json().get("href")

            with open(local_file_path, "rb") as file_bytes:
                put_response = requests.put(secret_upload_url, data=file_bytes)

                if put_response.status_code == 201:
                    print(f"Файл '{local_file_path}' успешно загружен в папку '{folder_name}'!")
                    return True
                else:
                    print(f"Ошибка загрузки файла. Статус: {put_response.status_code}")
                    return False
        else:
            print(f"Не удалось получить ссылку на загрузку. Статус-код: {response.status_code}")
            return False


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, ".env")
    load_dotenv(env_path)

    YANDEX_TOKEN = os.getenv("YANDEX_TOKEN", "")
    print(f"Системный лог: Считано символов токена — {len(YANDEX_TOKEN)}")

    detector = IpDetector()
    my_ip = detector.get_current_ip()
    print(f"My IP address: {my_ip}")

    if my_ip:
        info_provider = IpInfoProvider()
        geo_data = info_provider.get_location_info(my_ip)
        print(f"My GEO data: {geo_data}")

        clean_data = {my_ip: geo_data['city']}

        with open("visit_info.json", "w", encoding="utf-8") as file:
            json.dump(clean_data, file, ensure_ascii=False, indent=4)
        print("Файл успешно создан!")

        uploader = YandexDiskUploader(YANDEX_TOKEN)
        uploader.create_folder("IpDetector")
        upload_success = uploader.upload_file("IpDetector", "visit_info.json")

        if upload_success:
            if os.path.exists("visit_info.json"):
                os.remove("visit_info.json")
                print("Локальный файл visit_info.json успешно удален.")


if __name__ == "__main__":
    main()
    