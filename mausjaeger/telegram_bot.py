import time
import os
import settings
import boto3
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)

CHAT_ID = settings.get_chat_id()
BOT_TOKEN = settings.get_bot_token()

aws_access_key_id = settings.get_aws_access_key_id()
aws_secret_access_key = settings.get_aws_secret_access_key()
aws_region = "eu-central-1"

commands = [
    "/help",
    "/reboot",
    "/shutdown",
    "/delete",
    "/pause",
    "/resume",
]


def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    help_handler = CommandHandler("help", bot_help_cmd)
    application.add_handler(help_handler)
    # send_pic_handler = CommandHandler("sendlivepic", bot_send_live_pic_cmd)
    # application.add_handler(send_pic_handler)
    reboot_handler = CommandHandler("reboot", bot_reboot_cmd)
    application.add_handler(reboot_handler)
    shutdown_handler = CommandHandler("shutdown", bot_shutdown_cmd)
    application.add_handler(shutdown_handler)
    delete_handler = CommandHandler("delete", bot_delete_cmd)
    application.add_handler(delete_handler)
    pause_handler = CommandHandler("pause", bot_pause_cmd)
    application.add_handler(pause_handler)
    resume_handler = CommandHandler("resume", bot_resume_cmd)
    application.add_handler(resume_handler)
    rate_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), bot_rate)
    application.add_handler(rate_handler)
    application.run_polling()


async def bot_help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_message = "Following commands supported:"
    for command in commands:
        bot_message += "\n " + command
    await context.bot.send_message(chat_id=update.effective_chat.id, text=bot_message)


async def bot_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message.caption.startswith("images/image"):
        rate = update.message.text
        if rate == "👍":
            mouse_detected = 1
            text = "Mimi mit Maus!"
        if rate == "👎":
            mouse_detected = 0
            text = "Mimi ohne Maus!"
        if rate == "👌":
            mouse_detected = -1
            text = "Keine Katze!"
    move_file(update.message.reply_to_message.caption, mouse_detected)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)


async def bot_delete_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Specify the S3 bucket name and the file you want to upload
    bucket_name = "mousehunter"
    # Create an S3 client
    s3 = boto3.client(
        "s3",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=aws_region,
    )

    # List all objects in the bucket
    objects = s3.list_objects_v2(Bucket=bucket_name)

    # Check if there are objects in the bucket
    counter = 0
    if "Contents" in objects:
        # Filter for .jpg files and delete each one
        for obj in objects["Contents"]:
            key = obj["Key"]
            if key.endswith(".jpg") and "/" not in key:
                counter += 1
                s3.delete_object(Bucket=bucket_name, Key=key)

    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=f"{counter} Images deleted!"
    )


def move_file(file: str, mouse_detected):
    # Specify the S3 bucket name and the file you want to upload
    bucket_name = "mousehunter"
    # Create an S3 client
    s3 = boto3.client(
        "s3",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=aws_region,
    )

    if mouse_detected == 1:
        folder = "mit"
    elif mouse_detected == 0:
        folder = "ohne"
    else:
        folder = "keine"

    file = file.split("/")
    source = f"{bucket_name}/{file[1]}"
    destination = f"{folder}/{file[1]}"
    # destination = f"{bucket_name}/{folder}/{file[1]}"

    s3.copy_object(
        Bucket=bucket_name,
        CopySource=source,
        Key=destination,
    )

    # Delete the original file
    s3.delete_object(Bucket=bucket_name, Key=file[1])


async def bot_reboot_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for i in range(5):
        time.sleep(1)
        bot_message = "Rebooting in " + str(5 - i) + " seconds..."
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=bot_message
        )
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="See ya later Alligator 🐊🐊🐊"
    )
    os.system("sudo reboot")


async def bot_shutdown_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="SHUTDOWN 💀💀💀"
    )
    os.system("sudo shutdown -h now")


async def bot_pause_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Pause")
    os.system("sudo systemctl stop mausjaeger.service")


async def bot_resume_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Resume")
    os.system("sudo systemctl start mausjaeger.service")


def bot_prey_cmd(bot, update):
    pass


def bot_noprey_cmd(bot, update):
    pass


async def send_text(message, update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)


def send_img(img, caption, update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.bot.send_photo(
        chat_id=update.effective_chat.id, photo=open(img, "rb"), caption=caption
    )


if __name__ == "__main__":
    main()
