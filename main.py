from asyncio.tasks import current_task
from typing import Dict
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ContentType
from aiogram.filters import CommandStart
from aiogram.methods import send_video
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    Message,
    InlineKeyboardMarkup,
)
import os
import asyncio
from time import time
from task_queue import TaskQueue, Task
from videoedit import cropvideo, speedupvideo
import subprocess

bot = Bot(token=os.environ["TG_BOT_TOKEN"])
dp = Dispatcher()
queue = TaskQueue()

# A dictionary to store user states for operations
user_states: Dict[int, Dict] = {}
# A dictionary to track queue position messages
queue_position_messages: Dict[str, Message] = {}


@dp.message(CommandStart())
async def command_start_handler(msg: Message) -> None:
    print("[ Start ]")

    github_button = InlineKeyboardButton(
        text="👨🏼‍💻Github", url="https://github.com/fobbidennotis/telegramEditorBot"
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[[github_button]])

    await msg.answer(
        text=(
            "Hey, I am a telegram bot for easy and fast video editing (yet another ffmpeg wrapper lol). "
            "Just drop me your video. I am also open-source, so you can self-host me."
        ),
        reply_markup=markup,
    )


@dp.message(F.content_type == ContentType.VIDEO)
async def handle_video(msg: Message) -> None:
    crop_button = InlineKeyboardButton(text="Crop", callback_data="crop")
    speed_button = InlineKeyboardButton(text="Modify speed", callback_data="speed")
    concat_button = InlineKeyboardButton(text="Concat", callback_data="concat")

    markup = InlineKeyboardMarkup(
        inline_keyboard=[[crop_button], [speed_button], [concat_button]]
    )

    await msg.reply(
        text="Alright, now choose an action to perform from below", reply_markup=markup
    )


@dp.callback_query()
async def handle_video_operation_choice(query: CallbackQuery) -> None:
    if query.message.reply_to_message and query.message.reply_to_message.video:
        # Save the operation state for the user
        user_states[query.from_user.id] = {
            "action": query.data,
            "video": query.message.reply_to_message.video,
            "chat_id": query.message.chat.id,
        }

        if query.data == "speed":
            await query.message.reply(
                text="Send me a speed multiplier (e.g., 2 for double speed, 0.5 for half speed).",
                parse_mode="Markdown",
            )
        else:
            await query.message.reply(
                text="Send me your timecodes AS A REPLY TO THIS MESSAGE in the format:\n`start;end`\n(e.g., `00:00:05;00:00:10`)",
                parse_mode="Markdown",
            )
    else:
        await query.answer("No video found in the replied message!", show_alert=True)


@dp.message(F.reply_to_message)
async def handle_timecodes(msg: Message) -> None:
    user_id = msg.from_user.id

    if user_id not in user_states:
        return

    state = user_states[user_id]
    video = state["video"]

    try:
        # Create a task and add it to the queue
        task_id = f"{time()}_{user_id}_{msg.message_id}"
        queue.push(
            Task(
                action=f'{state["action"]}/{msg.text}' if msg.text else state["action"],
                task_id=task_id,
                chat_id=state["chat_id"],
                video_file_id=video.file_id,
            )
        )

        # Send queue position message
        queue_pos = queue.get_pos(task_id)
        position_msg = await msg.reply(
            f"Your task is in position {queue_pos + 1} of the queue."
        )
        queue_position_messages[task_id] = position_msg

    except Exception as e:
        print(f"Error: {e}")
        await msg.reply(
            "Invalid input or an error occurred. Please ensure your input is in the correct format."
        )
    finally:
        user_states.pop(user_id, None)


async def update_queue_positions():
    """Update queue position messages for all queued tasks"""
    while True:
        for task_id, msg in list(queue_position_messages.items()):
            queue_pos = queue.get_pos(task_id)
            if queue_pos is not None:
                try:
                    await msg.edit_text(
                        f"Your task is in position {queue_pos + 1} of the queue."
                    )
                except Exception as e:
                    print(f"Error updating queue position: {e}")
            else:
                # Task is no longer in queue, remove the message tracking
                queue_position_messages.pop(task_id, None)
        await asyncio.sleep(5)  # Update every 5 seconds


async def poll_queue() -> None:
    """Continuously poll the queue for tasks."""
    print("[ Queue Polling Started ]")
    while True:
        current_task: Task = queue.top()
        if current_task:
            try:
                print(f"Processing task: {current_task.task_id}")

                # Download the video
                save_path = f"./vids/input/{current_task.task_id}.mp4"
                await bot.download(current_task.video_file_id, destination=save_path)

                # Wait a bit to ensure file is fully downloaded
                await asyncio.sleep(1)

                # Verify file size
                if os.path.getsize(save_path) == 0:
                    raise ValueError("Downloaded file is empty")

                # Determine action and process video
                action_parts = current_task.action.split("/")
                match action_parts[0]:
                    case "crop":
                        output_file_path = cropvideo(
                            video_path=save_path,
                            timecodes=action_parts[1],
                            id=current_task.task_id,
                        )
                    case "speed":
                        output_file_path = speedupvideo(
                            video_path=save_path,
                            speed=float(action_parts[1]),
                            id=current_task.task_id,
                        )
                    case _:
                        print(f"Unknown action: {current_task.action}")
                        queue.pop()
                        continue

                # Send the processed video
                await bot.send_video(
                    current_task.chat_id, video=FSInputFile(output_file_path)
                )

                # Remove the task and delete temp files
                os.remove(output_file_path)
                os.remove(f"./vids/input/{current_task.video_file_id}.mp4")
                print(f"Task {current_task.task_id} completed and removed from queue.")
            except Exception as e:
                print(f"Error processing task {current_task.task_id}: {e}")
                # Optionally, send an error message to the user
                try:
                    await bot.send_message(
                        current_task.chat_id,
                        f"Sorry, there was an error processing your video: {str(e)}",
                    )
                except Exception:
                    pass
            finally:
                # Remove position tracking message
                task_id = current_task.task_id
                if task_id in queue_position_messages:
                    try:
                        await queue_position_messages[task_id].delete()
                    except Exception:
                        pass
                queue_position_messages.pop(task_id, None)
                queue.pop()
        else:
            await asyncio.sleep(10)


async def main() -> None:
    print("[ Main ]")

    asyncio.create_task(poll_queue())
    asyncio.create_task(update_queue_positions())

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
