from typing import Dict, List
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ContentType
from aiogram.filters import CommandStart
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    Message,
    InlineKeyboardMarkup,
    video,
)
import os
import asyncio
from time import time
from task_queue import TaskQueue, Task
from videoedit import cropvideo, speedupvideo, mergevideos


bot = Bot(token=os.environ["TG_BOT_TOKEN"])
dp = Dispatcher()
queue = TaskQueue()

user_states: Dict[int, Dict] = {}
queue_position_messages: Dict[str, Message] = {}


@dp.message(CommandStart())
async def command_start_handler(msg: Message) -> None:
    print("[ Start ]")

    github_button = InlineKeyboardButton(
        text="👨🏼‍💻Github", url="https://github.com/fobbidennotis/telegram-editor-bot"
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
    print("called1")
    if msg.reply_to_message:
        if "concat" in msg.reply_to_message.text:
            print("bebra")
            await handle_timecodes(msg)
            return

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
        user_states[query.from_user.id] = {
            "action": query.data,
            "videos": [query.message.reply_to_message.video.file_id],
            "chat_id": query.message.chat.id,
        }
        print(user_states)

        match query.data:
            case "speed":
                await query.message.reply(
                    text="Send me a speed multiplier AS A REPLY TO THIS MESSAGE (e.g., 2 for double speed, 0.5 for half speed).",
                    parse_mode="Markdown",
                )
            case "crop":
                await query.message.reply(
                    text="Send me your timecodes AS A REPLY TO THIS MESSAGE in the format:\nstart;end\n(e.g., 00:00:05;00:00:10)",
                    parse_mode="Markdown",
                )
            case "concat":
                await query.message.reply(
                    text="Send me your videos one by one as replies to this message, they will be concatenated in the order in which you send them. When all videos are sent, send 'merge' as a reply to this same message in order to concatenate the sent videos.",
                    parse_mode="Markdown",
                )
    else:
        await query.answer("No video found in the replied message!", show_alert=True)


@dp.message(F.reply_to_message)
async def handle_timecodes(msg: Message) -> None:
    print("called")
    user_id = msg.from_user.id

    if user_id not in user_states:
        return

    state = user_states[user_id]
    videos = state["videos"]

    if msg.reply_to_message:
        print(msg.reply_to_message.text)
        print("1")
        if msg.text:
            if "merge" in msg.text.lower():
                pass
        elif "concatenated" in msg.reply_to_message.text:
            print(msg.reply_to_message.text)
            videos.append(msg.video.file_id)
            print(videos)

            return

    try:
        task_id = f"{time()}_{user_id}_{msg.message_id}"
        queue.push(
            Task(
                action=f'{state["action"]}/{msg.text}' if msg.text else state["action"],
                task_id=task_id,
                chat_id=state["chat_id"],
                video_file_id=videos,
            )
        )

        queue_pos = queue.get_pos(task_id)
        position_msg = await msg.reply(
            f"Your task is in position {queue_pos} of the queue."
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
                queue_position_messages.pop(task_id, None)
        await asyncio.sleep(5)


async def poll_queue() -> None:
    """Continuously poll the queue for tasks."""
    print("[ Queue Polling Started ]")
    while True:
        current_task: Task = queue.top()
        if current_task:
            try:
                print(f"Processing task: {current_task.task_id}")

                save_path: str = ""
                saved_videos: List[str] = []

                for i in range(len(current_task.video_file_id)):
                    save_path = f"./vids/input/{current_task.task_id}_{i}.mp4"
                    await bot.download(
                        current_task.video_file_id[i], destination=save_path
                    )
                    saved_videos.append(save_path)

                await asyncio.sleep(1)

                if os.path.getsize(save_path) == 0:
                    raise ValueError("Downloaded file is empty")

                action_parts = current_task.action.split("/")
                match action_parts[0]:
                    case "crop":
                        output_file_path = cropvideo(
                            video_path=saved_videos[0],
                            timecodes=action_parts[1],
                            id=current_task.task_id,
                        )
                    case "speed":
                        output_file_path = speedupvideo(
                            video_path=saved_videos[0],
                            speed=float(action_parts[1]),
                            id=current_task.task_id,
                        )
                    case "concat":
                        output_file_path = mergevideos(
                            videos_path=saved_videos, id=current_task.task_id
                        )
                    case _:
                        print(f"Unknown action: {current_task.action}")
                        queue.pop()
                        continue

                await bot.send_video(
                    current_task.chat_id, video=FSInputFile(output_file_path)
                )

                os.remove(output_file_path)

                for filename in saved_videos:
                    os.remove(filename)
                print(f"Task {current_task.task_id} completed and removed from queue.")
            except Exception as e:
                print(f"Error processing task {current_task.task_id}: {e}")
                try:
                    await bot.send_message(
                        current_task.chat_id,
                        f"Sorry, there was an error processing your video: {str(e)}",
                    )
                except Exception:
                    pass
            finally:
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
