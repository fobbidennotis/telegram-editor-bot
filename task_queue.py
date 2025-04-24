from typing import List
from dataclasses import dataclass


@dataclass
class Task:
    task_id: str
    chat_id: int
    action: str
    video_file_id: List[str]  # Changed from video_path to video_file_id


class TaskQueue:
    def __init__(self) -> None:
        self.queue: List[Task] = []

    def push(self, task: Task) -> None:
        self.queue.append(task)

    def pop(self) -> None:
        if self.queue:
            self.queue.pop(0)

    def top(self) -> Task | None:
        if self.queue:
            return self.queue[0]
        return None

    def get_pos(self, search_id) -> int | None:
        for index, task in enumerate(self.queue):
            if task.task_id == search_id:
                return index
        return None
