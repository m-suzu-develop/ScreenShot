import io
from time import sleep
from typing import List, Tuple, Optional
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import os
import datetime
import configparser
import json
import logging

def get_full_screenshot_image(driver, reverse=False, driverss_contains_scrollbar=None):
    if driverss_contains_scrollbar is None:
        driverss_contains_scrollbar = isinstance(driver, webdriver.Chrome)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    sleep(0.5)
    scroll_height, document_client_width, document_client_height, inner_width, inner_height = driver.execute_script("return [document.body.scrollHeight, document.documentElement.clientWidth, document.documentElement.clientHeight, window.innerWidth, window.innerHeight]")
    streams_to_be_closed = []
    images = []
    try:
        for y_coord in range(0, scroll_height, document_client_height):
            driver.execute_script("window.scrollTo(0, arguments[0]);", y_coord)
            stream = io.BytesIO(driver.get_screenshot_as_png())
            streams_to_be_closed.append(stream)
            img = Image.open(stream)
            images.append((img, min(y_coord, scroll_height - inner_height)))
        scale = float(img.size[0]) / (inner_width if driverss_contains_scrollbar else document_client_width)
        img_dst = Image.new(mode='RGBA', size=(int(document_client_width * scale), int(scroll_height * scale)))
        for img, y_coord in (reversed(images) if reverse else images):
            img_dst.paste(img, (0, int(y_coord * scale)))
        return img_dst
    finally:
        # close
        for stream in streams_to_be_closed:
            stream.close()
        for img, y_coord in images:
            img.close()

try:
    print("-----------------------------------Program Start------------------------------------------------------")
    #logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    h1 = logging.StreamHandler()
    h1.setLevel(logging.DEBUG)
    log_dir = os.path.dirname(__file__) + "\log"
    log_path = os.path.join(log_dir, str(datetime.datetime.now().strftime("%Y%m%d%H%M%S")) + '.log')
    h2 = logging.FileHandler(log_path)
    h2.setLevel(logging.ERROR)
    fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # ハンドラーにフォーマッターを設定する
    h1.setFormatter(fmt)
    h2.setFormatter(fmt)
    
    # ロガーにハンドラーを設定する
    logger.addHandler(h1)
    logger.addHandler(h2)

    #config
    logger.debug("config read")
    config_ini = configparser.ConfigParser()
    config_ini_name = 'config.ini'
    config_dir = os.path.dirname(__file__) + "\config"
    config_ini_path = os.path.join(config_dir, config_ini_name)
    if not os.path.exists(config_ini_path):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), config_ini_path)
    config_ini.read(config_ini_path, encoding='utf-8')
    UrlList = config_ini.get('Config', 'UrlList')
    UrlList = json.loads(UrlList)
    DriverPath = config_ini.get('Config', 'ChromeDriverDir')

    logger.debug("driver option setting")
    options = Options()
    options.add_argument('--headless')
    driver = webdriver.Chrome(executable_path=DriverPath,options=options)

    # create output older
    logger.debug("create output folder")
    folder_name = "output_" + str(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
    os.mkdir(folder_name)

    # create screenShot
    logger.debug("create screenShot")
    for url in UrlList:
        driver.get(url)
        sleep (5)
        logger.debug("url open wait 5 second")
        img = get_full_screenshot_image(driver) 
        img_name = folder_name + '/' +  url.lstrip("https://" "http://" ).replace("/","").replace("?", "").replace("&", "").replace("=", "").replace(".", "")  + ".png"
        img.save(img_name)
        logger.debug("save png")

    logger.debug("Program End")
except Exception as e:
    logger.error(e)
    logger.error("Program error End")
