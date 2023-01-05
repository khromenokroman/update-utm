#!/usr/bin/env python3

#Необходимо перед запуском
#apt update && apt install pip -y & pip install requests && pip install lxml && pip install bs4 && chmod +x ./update_utm.py
#также нужен ФПТ сервер (продублировать и на фтп и в локальной папке)
# в папке с основным скриптом создать файл ftp_config_raipo.py
# Такого вида:
# local_path = '/home/raipo' #путь где находится скрипт
# ftp_host = '192.168.1.33' #адрес фтп
# ftp_login = 'utm12345' #логин фтп
# ftp_password = 'utm12345' #пароль фтп
# ftp_folder = 'pikachu/betmen/123' #путь до папки с которой нужно все скачивать (пакет утм, обновление скрипта)
# url_telegramm = https://api.telegram.org/bot209634589:AAEPr6M63344550JsNbGCLiGH6ZYDU/sendMessage?chat_id=311391144&parse_mode=html&text=
# также на фтп должен быть файл version_new
# в первой строке должно быть указанно yes или no
# пакет с дистрибутивом назвать utm.deb положить на фтп

#свои библиотеки
from ftp_config_raipo import ftp_host, ftp_login, ftp_password, ftp_folder, local_path, url_telegramm

#штатные библиотеки
import os
from ftplib import FTP
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from time import sleep
#from progressbar import ProgressBar

class Ftp_raipo(): #Клас дял скачивание файла с ФТП
    
    def __init__(self, ftp_host, ftp_login, ftp_password):
        self.ftp_host = ftp_host
        self.ftp_login = ftp_login
        self.ftp_password = ftp_password
    
    def download_file(self, ftp_file_name, ftp_folder, local_path = '.'): #Подключается к FTP и скачивает файл
        try:
            with FTP(host = self.ftp_host, user = self.ftp_login, passwd = self.ftp_password) as ftp:
                ftp.cwd(ftp_folder) 
                print('\nFTP:\n' + '='*20)
                print(ftp.dir())
                print('='*20)
                targetFileName = ftp_file_name
                localFilePath = f'{local_path}/{targetFileName}'
                #скачаем файл инфо версии
                with open(localFilePath, 'wb') as file:
                    # ftp.voidcmd('TYPE I')
                    # size = ftp.size(ftp_file_name)
                    # pbar = ProgressBar(max_value = size)
                    # pbar.start()
                    # def file_write(data):
                    #     file.write(data)
                    #     pbar.value += len(data)
                    #     pbar.update()
                    # restCode = ftp.retrbinary(f'RETR {targetFileName}', file_write, blocksize= 1024)
                    print(f'Скачиваю файл {ftp_file_name} ...')
                    restCode = ftp.retrbinary(f'RETR {targetFileName}', file.write, blocksize= 1024)

                #проверим скачался файл или нет
                if restCode.startswith('226'):
                    print(f'\nСкачивание файла {ftp_file_name} завершено успешно!\n')
                    return '226'
                else:
                    print('Скачивание файла не успешно!!!')
                    return '0'
        except Exception as ex:
            print(ex)
            return '0'

class Service_update(Ftp_raipo): #Клас выполняющий сервисные функции для основного скрипта обновления
    
    def __init__(self, local_path):
        Ftp_raipo.__init__(self, ftp_host, ftp_login, ftp_password)
        self.local_path = local_path

    def check_file_log(self): #проверка файла в каталоге если он большой то удалим
        size_log = 0
        try:
            with open(f'{self.local_path}/update_log') as file:
                text_file = file.readlines()
                size_log = len(text_file)
            if size_log > 1000:
                os.system(f'rm {self.local_path}/update_log')
                print('Лог файл удален!')
            else:
                print('Лог файл ок!')
        except Exception as ex:
            print(ex)
    
    def get_service_utm_status(self): # 0 -сервиз запущен, 1024 - сервис не установлен, 768 - севис установлен но есть ошибка, error - остальные ошибки
        return os.system('sudo supervisorctl status utm')
    
    def run_comands_terminal_del(self): #Выполняет команды удаления
        print('apt remove u-trans -y')
        os.system('apt remove u-trans -y') #удалим установленный УТМ
        print('rm -r /opt/utm/')
        os.system('rm -r /opt/utm/') #удалим каталог УТМ
        print('rm -r home/raipo/u-trans*')
        os.system('rm -r home/raipo/u-trans*') #удалим пакеты с каталога
        print('rm -r home/raipo/utm*')
        os.system('rm -r home/raipo/utm*')
        print('sudo apt install acl -y')
        os.system('sudo apt install acl -y')

    def send_message_telegram(self,version_utm_host = '-',version_utm_server = '-', result = '-'): #Отправляет сообщение боту в телеграм
        name_pc = os.uname()[1]
        inet_conf = os.system(f'ip addr | grep "inet 192.168." > {self.local_path}/ip_conf')
        with open(f'{self.local_path}/ip_conf') as file_ip:
            list_line = file_ip.readlines()
        ip_adress = list_line[0].strip().split(' ')[1][:-3]
        utm_info = self.getInfoUTM(ip_adress)
        if version_utm_server == 'yes' and result == '-':
            message_telega = f'🛒Магазин: <b>{name_pc}</b>\n📡IP: <b>{ip_adress}:8080</b>\n🏷Ver. UTM: <b>{version_utm_host}</b>\n🖥Команда для обновления УТМ: <b>{version_utm_server}</b>\n{utm_info}\n<b>❗️ТРЕБУЕТСЯ ОБНОВЛЕНИЕ❗️</b>'
            url_telega = f'{url_telegramm}{message_telega}'
            response = requests.get(f'{url_telega}')
        elif result == 'ok':
            message_telega = f'🛒Магазин: <b>{name_pc}</b>\n📡IP: <b>{ip_adress}:8080</b>\n{utm_info}\n<b>❗️УТМ обновлен❗️</b>'
            url_telega = f'{url_telegramm}{message_telega}'
            response = requests.get(f'{url_telega}')
        else:
            message_telega = f'🛒Магазин: <b>{name_pc}</b>\n📡IP: <b>{ip_adress}:8080</b>\n🏷Ver. UTM: <b>{version_utm_host}</b>\n🖥Команда для обновления УТМ: <b>{version_utm_server}</b>\n{utm_info}\n<b>❗️ОБНОВЛЕНИЕ НЕ ТРЕБУЕТСЯ❗️</b>'
            url_telega = f'{url_telegramm}{message_telega}'
            response = requests.get(f'{url_telega}')
        print('Сообщение Telegram отправлено!')

    def check_version_utm(self, path): #Получает версию утм хоста

        try:
            print('Получаем текущую версию утм...')
            with open('/opt/utm/transport/l/transport_info.log') as file:
                file.seek(0)
                version_line = ''
                file_line = file.readlines()
                check_line = 'UTM-Version:'
                print(f'Всего строк в документе: {len(file_line)}')
                for line in file_line:
                    if line.find(check_line) != -1:
                        # print(f'{line}\n{len(line)}')
                        version_line = line.strip()
                    else:
                        continue
                    # print(version_line)
                versionUTM = version_line[len(version_line)-13:len(version_line)-1]
                print(f'Текущая версия УТМ: {versionUTM}')
            
            try:
                with open(f'{path}/version_utm') as file_utm:
                    version_local_utm = file_utm.readlines()[0]
                if len(versionUTM.strip()) > 5:
                    with open(f'{path}/version_utm', 'w+') as file_utm:
                        file_utm.write(versionUTM)
                return versionUTM
            except:
                with open(f'{path}/version_utm', 'w+') as file_utm:
                    file_utm.write(versionUTM)
                return versionUTM
        except Exception as ex:
            file_log.write(str(ex))
            return '-'

    def download_file_service(self, ftp_folder, local_path): #Скачиваем файлы для обслуживания обновления
        raipo_ftp = Ftp_raipo(ftp_host, ftp_login, ftp_password)
        print('Обновляю служебные файлы ...')
        dwn_script = raipo_ftp.download_file('update_utm.py', ftp_folder, local_path)
        cfg = raipo_ftp.download_file('ftp_config_raipo.py', ftp_folder, local_path)

    def getInfoUTM(self, adress):
        #adress = '192.168.11.20'
        try:
            link_key = f'http://{adress}:8080/api/info/list'
            link_adres = f'http://{adress}:8080/api/rsa'
            #print(link_adres)
            #print(link_key)
            answer_key = requests.get(link_key).text
            answer_adress = requests.get(link_adres).json()
            #print(answer_key)
            #print(answer_adress)
            soup = BeautifulSoup(answer_key,'lxml')
            block = soup.find_all('p')[0].text
            blockCR = block.split(':')
            #print(blockCR)
            fsrar_temp = blockCR[5].split('"')
            fsrar = fsrar_temp[1]

            rsa = blockCR[16][1:11]

            gost = blockCR[26][1:11]

            answer_adress = requests.get(link_adres).json()
            data = answer_adress['rows']
            #print(answer_adress)
            owner_id = 'Owner_ID'
            short_name = 'Short_Name'
            inn = 'INN'
            kpp = 'KPP'
            fact_address = 'Fact_Address'

            for i in data:
                if i[owner_id] == fsrar:
                    str_info = f'🏘Организация: <b>{i[short_name]}</b>\n🚦ИНН/КПП: <b>{i[inn]}/{i[kpp]}</b>\n<b>🐽Адрес:</b> {i[fact_address]}\n🚨Сертификат: <b>{fsrar}</b>\n🍻RSA: <b>{rsa}</b>\n🍻GOST: <b>{gost}</b>'
                    print(str_info)
                    return str_info
        except Exception as ex:
            print(ex)
            print('Ошибка получения инфо об УТМ')
            return '-'

if __name__ == '__main__':

    raipo_ftp = Ftp_raipo(ftp_host, ftp_login, ftp_password)
    task_utm = Service_update(local_path)


    #Смотрим директорию с логом
    task_utm.check_file_log()

    #Пишем лог
    with open(f'{local_path}/update_log', 'a+') as file_log:
        file_log.write('\n' + str(datetime.now()) + ': Запускаю процедуру обновления УТМ\n')

        status_utm = task_utm.get_service_utm_status()
        if status_utm != 0:
            try:
                file_log.write('УТМ не установлен либо имеются ошибки при работе!\n')
                print('УТМ не установлен либо имеются ошибки при работе!')
                task_utm.run_comands_terminal_del()
                ftp_file_name = 'utm.deb'
                restCode = raipo_ftp.download_file(ftp_file_name, ftp_folder, local_path)
                if restCode == '226':
                    os.system('ls -l -h')
                    file_log.write(f'Скачивание файла {ftp_file_name} завершено!\n')
                    os.system(f'apt install {local_path}/{ftp_file_name} -y') #устанавливаю утм
                    print('Ждем запуск утм...')
                    sleep(180)
                    file_log.write('Отправляю сообщегние в телегу (обновление успешно)...\n')
                    task_utm.send_message_telegram(result='ok')
                    task_utm.download_file_service(ftp_folder, local_path)
                else:
                    file_log.write('УТМ не установлен либо имеются ошибки при работе!\nОбновляю служебные файлы...')
                    print('Ошибка при скачивании файла!')
                    task_utm.download_file_service(ftp_folder, local_path)
            except Exception as ex:
                print(ex)
                file_log.write('Установка УТМ прошла с ошибкой!\nОбновляю служебные файлы...')
                task_utm.download_file_service(ftp_folder, local_path)
        else:
            try:
                #скачиваем version_new
                ftp_file_name = 'version_new'
                restCode = raipo_ftp.download_file(ftp_file_name, ftp_folder, local_path)
                #проверим скачался файл или нет
                if restCode == '226':
                    file_log.write('Скачивание файл-флага завершено успешно!\n\n')
                    file_log.write('!'*20 + '\n')
                    #смотрим текущую версию УТМ
                    versionUTM = task_utm.check_version_utm(local_path)
                    with open(f'{local_path}/version_new') as file:
                        data = file.readlines()[0]
                        #print(data)
                    print(f'Команда обновления с сервера: {data}')
                    with open(f'{local_path}/version_utm') as f:
                        version_utm_file = f.readlines()[0]
                    print(f'Версия УТМ в файле: {version_utm_file}')
                    # первая строка версия
                    file_log.write(f'Версия установленного УТМ: {versionUTM}\nВерсия УТМ на сервере {data}')
                    file_log.write('!'*20 + '\n\n')
                    if data.strip() == 'yes':
                        file_log.write('Отправляю сообщегние в телегу (надобы обновиться)...\n')
                        task_utm.send_message_telegram(version_utm_host=version_utm_file.strip(), version_utm_server=data.strip())
                        file_log.write('Версии различаются будет произведено обновление УТМ\n')
                        file_log.write('Проверим и удалим предыдущие версии УТМ...\n')
                        task_utm.run_comands_terminal_del()
                        #скачиваем utm.deb
                        ftp_file_name = 'utm.deb'
                        restCode = raipo_ftp.download_file(ftp_file_name, ftp_folder, local_path)
                        if restCode == '226':
                            file_log.write('Новая версия утм скачана успешно!!!\n')
                            os.system('ls -l') #смотрю директорию
                            os.system(f'apt install {local_path}/{ftp_file_name} -y') #устанавливаю утм
                            print('Ждем запуск утм...')
                            sleep(180)
                            file_log.write('Отправляю сообщегние в телегу (обновление успешно)...\n')
                            task_utm.send_message_telegram(version_utm_host=versionUTM.strip(), version_utm_server=data.strip(), result='ok')
                        else:
                            file_log.write('Скачивание не успешно...\nОбновляю служебные файлы...')
                            task_utm.download_file_service(ftp_folder, local_path)
                    else:
                        print('Установлена актуальная версия, обновление не требуется!')
                        file_log.write('Установлена актуальная версия, обновление не требуется!\nОбновляю служебные файлы...')
                        task_utm.send_message_telegram(version_utm_host=versionUTM.strip(), version_utm_server=data.strip())
                        task_utm.download_file_service(ftp_folder, local_path)
                else:
                    file_log.write('Скачивание файл-флага с FTP произошло с ошибкой!\nОбновляю служебные файлы...')
                    task_utm.download_file_service(ftp_folder, local_path)
            except:
                task_utm.download_file_service(ftp_folder, local_path)

