import os
import csv
import whois
import asyncio
from urllib.parse import urlparse
import aiofiles

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
sem = asyncio.Semaphore(100)  # количество одновременных проверок


async def get_domain(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


async def check_domain(domain, count, total_count):
    async with sem:
        try:
            result = await asyncio.to_thread(whois.whois, domain)
            if result.status is None:
                print(f'[{count}/{total_count}] Домен {domain} - свободен.')
                return True
            else:
                print(f'[{count}/{total_count}] Домен {domain} - занят.')
                return False
        except Exception as e:
            if 'No match for' in str(e):
                print(
                    f'[{count}/{total_count}] Домен {domain} - свободен (ошибка проверки).')
                return True
            else:
                print(f'Ошибка при проверке домена {domain}: {e}')
                return None


async def write_to_file_async(filename, data):
    async with aiofiles.open(filename, 'a', encoding='utf-8') as file:
        await file.write(data + '\n')


async def main():
    input_filename = input(
        "Введите имя входного файла (например, input.csv): ")
    base_filename = input_filename.rsplit('.', 1)[0]
    output_folder = base_filename
    os.makedirs(output_folder, exist_ok=True)
    output_filename = os.path.join(
        output_folder, f"{base_filename}_output.csv")
    not_available_filename = os.path.join(
        output_folder, f"{base_filename}_not_availability.csv")
    available_filename = os.path.join(
        output_folder, f"{base_filename}_with_availability.csv")

    with open(input_filename, 'r', newline='', encoding='utf-8') as input_file:
        csv_reader = csv.DictReader(input_file)
        csv_reader.fieldnames = [name.replace(
            '\ufeff', '') for name in csv_reader.fieldnames]
        print("Названия столбцов:", csv_reader.fieldnames)
        unique_websites = set()
        all_data = []

        for row in csv_reader:
            title = row['Title']
            website = row['Website'].strip()
            if not website:
                continue
            domain = await get_domain(website)
            if domain not in unique_websites:
                unique_websites.add(domain)
                all_data.append([title, domain])

    async with aiofiles.open(output_filename, 'w', newline='', encoding='utf-8') as output_file:
        await output_file.write('Title,Website\n')
        for title, domain in all_data:
            await output_file.write(f'{title},{domain}\n')

    print(f"Данные успешно сохранены в '{output_filename}'.")

    available_writer = await aiofiles.open(available_filename, 'w', newline='', encoding='utf-8')
    not_available_writer = await aiofiles.open(not_available_filename, 'w', newline='', encoding='utf-8')

    await available_writer.write('Title,Website\n')
    await not_available_writer.write('Title,Website\n')

    tasks = []
    for count, (title, domain) in enumerate(all_data, start=1):
        tasks.append(check_domain(domain, count, len(all_data)))

    results = await asyncio.gather(*tasks)

    for (title, domain), available in zip(all_data, results):
        if available is True:
            await available_writer.write(f'{title},{domain}\n')
        elif available is False:
            await not_available_writer.write(f'{title},{domain}\n')
        else:
            print(f"Ошибка при проверке домена: {domain}")

    await available_writer.close()
    await not_available_writer.close()

    print(f"Данные с проверкой доступности доменов успешно сохранены в '{
          available_filename}' и '{not_available_filename}'")

asyncio.run(main())
