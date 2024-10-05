import os
import csv
import requests
from urllib.parse import urlparse

print("""
_________   _____________   ____ __________                                    
\\_   ___ \\ /   _____/\\   \\ /   / \\______   \\_____ _______  ______ __________  
/    \\  \\/ \\_____  \\  \\   Y   /   |     ___/\\__  \\_  __ \\/  ___// __ \\_  __ \\ 
\\     \\____/        \\  \\     /    |    |     / __ \\|  | \\/\\___ \\  ___/|  | \\/ 
 \\______  /_______  /   \\___/     |____|    (____  /__|  /____  >\\___  >__|    
        \\/        \\/                             \\/           \\/     \\/        
        ___.           _____.___.           .__                                
        \\_ |__ ___.__. \\__  |   | _______  _|  |__   ____   ____               
         | __ <   |  |  /   |   |/ __ \\  \\/ /  |  \\_/ __ \\ /    \\              
         | \\_\\ \\___  |  \\____   \\  ___/\\   /|   Y  \\  ___/|   |  \\             
         |___  / ____|  / ______|\\___  >\\_/ |___|  /\\___  >___|  /             
             \\/\\/       \\/           \\/          \\/     \\/     \\/               
""")


def get_domain(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def is_domain_available(domain):
    url = "https://domainstatus.p.rapidapi.com/v1/domain/available"
    domain_parts = domain.split('.')
    if len(domain_parts) < 2:
        print(f"Некорректный домен: {domain}")
        return None
    name = domain_parts[0]
    tld = '.'.join(domain_parts[1:])
    payload = {
        "name": name,
        "tld": tld
    }
    headers = {
        "x-rapidapi-key": "581ef0380fmshe8c5295e6f21046p1e2b6ejsnd813cb35d4fb",
        "x-rapidapi-host": "domainstatus.p.rapidapi.com",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response_data = response.json()
        print(f"Проверка домена: {domain}, Ответ: {response_data}")
        return response_data.get('available', False)
    except requests.RequestException as e:
        print(f"Ошибка при проверке домена {domain}: {e}")
        return None


input_filename = input("Введите имя входного файла (например, input.csv): ")
base_filename = input_filename.rsplit('.', 1)[0]
output_folder = base_filename
os.makedirs(output_folder, exist_ok=True)
output_filename = os.path.join(output_folder, f"{base_filename}_output.csv")
not_available_filename = os.path.join(
    output_folder, f"{base_filename}_not_availability.csv")
available_filename = os.path.join(
    output_folder, f"{base_filename}_with_availability.csv")

with open(input_filename, 'r', newline='', encoding='utf-8') as input_file:
    csv_reader = csv.DictReader(input_file)
    csv_reader.fieldnames = [name.replace(
        '\ufeff', '') for name in csv_reader.fieldnames]
    unique_websites = set()
    all_data = []

    for row in csv_reader:
        title = row['Title']
        website = row['Website'].strip()
        if not website:
            continue
        domain = get_domain(website)
        if domain not in unique_websites:
            unique_websites.add(domain)
            all_data.append([title, domain])

    with open(output_filename, 'w', newline='', encoding='utf-8') as output_file:
        output_writer = csv.writer(output_file)
        output_writer.writerow(['Title', 'Website'])
        output_writer.writerows(all_data)

    print(f"Данные успешно сохранены в '{output_filename}'.")

    with open(available_filename, 'w', newline='', encoding='utf-8') as available_file, \
            open(not_available_filename, 'w', newline='', encoding='utf-8') as not_available_file:

        available_writer = csv.writer(available_file)
        not_available_writer = csv.writer(not_available_file)
        available_writer.writerow(['Title', 'Website'])
        not_available_writer.writerow(['Title', 'Website'])

        for title, domain in all_data:
            available = is_domain_available(domain)
            if available is True:
                available_writer.writerow([title, domain])
            elif available is False:
                not_available_writer.writerow([title, domain])
            else:
                print(f"Ошибка при проверке домена: {domain}")

print(f"Данные с проверкой доступности доменов успешно сохранены в '{
      available_filename}' и '{not_available_filename}'")
