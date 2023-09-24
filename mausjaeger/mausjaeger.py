import datetime
from logging import handlers

import RPi.GPIO as GPIO
import time
import logging
import picamera2 as picam2  # Importing the library for camera module
import signal
import asyncio
import telegram
import os
import boto3
from time import sleep
import settings


def exit_gracefully(signum, frame):
    logging.info("GRACEFUL EXIT ...")
    GPIO.cleanup()
    logging.info("GRACEFUL EXIT done.")
    exit()


async def send_notification(image) -> None:
    bot_token = settings.get_bot_token()
    chat_id = settings.get_chat_id()
    bot = telegram.Bot(token=bot_token)
    retries = 0
    while retries < 10:
        try:
            await bot.send_photo(
                chat_id=chat_id,
                photo=open(image, "rb"),
                caption=image,
                read_timeout=30,
                write_timeout=30,
            )
            break
        except telegram.error.TimedOut:
            retries += 1
            if retries < 10:
                sleep(1)


def MOTION(PIR_GPIO):
    capture_time = datetime.datetime.now()
    filename = f'images/image_{capture_time.strftime("%Y-%m-%d_%H_%M_%S")}'
    if datetime.datetime.now().hour in [
        0,
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
    ]:
        logger.info("Start Recording")
        files = []
        for i in range(0, 20):
            filename_timestamp = filename + "_" + str(i) + ".jpg"
            camera.switch_mode_and_capture_file(camera_config, filename_timestamp)
            files.append(filename_timestamp)
        for file in files:
            asyncio.run(send_notification(file))
        asyncio.run(upload(files))
        logger.info("Stop Recording")

    else:
        logger.info("Not recording, not in operating hours.")


async def upload(files) -> None:
    for upload_file in files:
        object_key = os.path.basename(upload_file)

        # Upload the file
        try:
            s3.upload_file(upload_file, bucket_name, object_key)
            os.remove(upload_file)
        except Exception as e:
            print(f"Error: {e}")


log_file = "logs/mausjaeger.log"
logging.basicConfig(filename=log_file)
logger = logging.getLogger()
logHandler = handlers.TimedRotatingFileHandler(
    log_file, when="D", interval=1, backupCount=5
)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger.setLevel(logging.INFO)
logHandler.setFormatter(formatter)
logHandler.setLevel(logging.INFO)
if logger.hasHandlers():
    logger.handlers.clear()
logger.addHandler(logHandler)


# Board Mode: Angabe der Pin-Nummer
GPIO.setmode(GPIO.BOARD)

# GPIO Pin definieren fuer den Dateneingang vom Sensor
PIR_GPIO = 12
GPIO.setup(PIR_GPIO, GPIO.IN)

# Specify your AWS credentials and region
aws_access_key_id = settings.get_aws_access_key_id()
aws_secret_access_key = settings.get_aws_secret_access_key
aws_region = "eu-central-1"

# Specify the S3 bucket name and the file you want to upload
bucket_name = "mousehunter"
# Create an S3 client
s3 = boto3.client(
    "s3",
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region,
)


camera = picam2.Picamera2()  # Setting up the camera
camera_config = camera.create_still_configuration(
    main={"size": (512, 384)}, lores={"size": (320, 180)}, display="lores"
)
camera.configure(camera_config)
# camera.resolution = (320, 180)
camera.framerate = 2
camera.start()

time.sleep(1)
logger.info("Motion detection activated")
time.sleep(1)
logger.info("**************************************")
signal.signal(signal.SIGTERM, exit_gracefully)
capture_time = datetime.datetime.now()

try:
    GPIO.add_event_detect(PIR_GPIO, GPIO.RISING, callback=MOTION)

    # MOTION(PIR_GPIO)

    while True:
        time.sleep(60)
finally:
    logger.info("Stopped .")
