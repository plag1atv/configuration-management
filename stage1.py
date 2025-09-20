import os
import shlex
import sys
import platform
from typing import List, Dict, Callable


class ShellEmulator:
    def __init__(self):
        self.username = os.getlogin()
        self.hostname = self.get_hostname()
        self.current_dir = "~"
        self.commands: Dict[str, Callable] = {
            'ls': self.cmd_ls,
            'cd': self.cmd_cd,
            'exit': self.cmd_exit
        }
        self.running = True

    def get_hostname(self) -> str:
        try:
            if platform.system() == "Windows":
                return os.environ.get('COMPUTERNAME', 'localhost')
            else:
                return os.uname().nodename
        except:
            return 'localhost'

    def get_prompt(self) -> str:
        return f"{self.username}@{self.hostname}:{self.current_dir}$ "

    def parse_arguments(self, command_line: str) -> List[str]:
        try:
            return shlex.split(command_line)
        except ValueError as e:
            print(f"Ошибка парсинга аргументов: {e}")
            return []

    def execute_command(self, command: str, args: List[str]) -> bool:
        if command in self.commands:
            try:
                self.commands[command](args)
                return True
            except Exception as e:
                print(f"Ошибка выполнения команды {command}: {e}")
                return False
        else:
            print(f"Неизвестная команда: {command}")
            return False

    def cmd_ls(self, args: List[str]) -> None:
        print(f"Команда: ls")
        print(f"Аргументы: {args}")

    def cmd_cd(self, args: List[str]) -> None:
        print(f"Команда: cd")
        print(f"Аргументы: {args}")
        if args:
            self.current_dir = args[0]

    def cmd_exit(self, args: List[str]) -> None:
        print("Завершение работы эмулятора")
        self.running = False

    def run(self):
        print("Добро пожаловать в эмулятор командной оболочки!")
        print("Для выхода введите 'exit'")
        print("-" * 50)
        while self.running:
            try:
                prompt = self.get_prompt()
                user_input = input(prompt).strip()
                if not user_input:
                    continue
                parts = self.parse_arguments(user_input)
                if not parts:
                    continue
                command = parts[0]
                args = parts[1:] if len(parts) > 1 else []
                self.execute_command(command, args)
            except KeyboardInterrupt:
                print("\nДля выхода введите 'exit'")
            except EOFError:
                print("\nЗавершение работы")
                break


def main():
    shell = ShellEmulator()
    shell.run()


if __name__ == "__main__":
    main()