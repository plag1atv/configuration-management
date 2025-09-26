import os
import shlex
import sys
import platform
import json
import base64
import argparse
from typing import List, Dict, Callable, Optional


class VFS:
    def __init__(self, vfs_path: str = None):
        self.vfs_path = vfs_path
        self.root = {}
        if vfs_path and os.path.exists(vfs_path):
            self.load_vfs(vfs_path)

    def load_vfs(self, vfs_path: str) -> None:
        """Загружает виртуальную файловую систему из JSON файла"""
        try:
            with open(vfs_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.root = data.get('root', {})
            print(f"DEBUG: VFS загружена из {vfs_path}")
            print(f"DEBUG: Корневая структура: {list(self.root.keys())}")
        except Exception as e:
            print(f"Ошибка загрузки VFS: {e}")
            self.root = {}

    def get_file_content(self, path: str) -> Optional[str]:
        """Получает содержимое файла из VFS"""
        parts = [p for p in path.split('/') if p]
        current = self.root.get('entries', {})

        for part in parts[:-1]:
            if part in current and current[part].get('type') == 'dir':
                current = current[part].get('entries', {})
            else:
                return None

        filename = parts[-1] if parts else ''
        if filename in current and current[filename].get('type') == 'file':
            content_b64 = current[filename].get('content', '')
            try:
                return base64.b64decode(content_b64).decode('utf-8')
            except:
                return content_b64
        return None

    def list_directory(self, path: str) -> List[str]:
        """Возвращает список содержимого директории в VFS"""
        if path == '/' or path == '':
            current = self.root.get('entries', {})
        else:
            parts = [p for p in path.split('/') if p]
            current = self.root.get('entries', {})

            for part in parts:
                if part in current and current[part].get('type') == 'dir':
                    current = current[part].get('entries', {})
                else:
                    return []

        return list(current.keys())


class ShellEmulator:
    def __init__(self, vfs_path: str = None, script_path: str = None):
        self.username = os.getlogin()
        self.hostname = self.get_hostname()
        self.current_dir = "~"
        self.vfs = VFS(vfs_path)
        self.script_path = script_path
        self.is_running_script = False

        # Отладочный вывод параметров
        print("DEBUG: Параметры запуска:")
        print(f"DEBUG: - VFS путь: {vfs_path}")
        print(f"DEBUG: - Скрипт путь: {script_path}")
        print("-" * 50)

        self.commands: Dict[str, Callable] = {
            'ls': self.cmd_ls,
            'cd': self.cmd_cd,
            'cat': self.cmd_cat,
            'pwd': self.cmd_pwd,
            'exit': self.cmd_exit,
            'echo': self.cmd_echo
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
            print(f"Неизвестная команда: {command}")  # ИСПРАВЛЕНО: было {e}, теперь {command}
            return False

    def cmd_ls(self, args: List[str]) -> None:
        path = args[0] if args else "."
        if path.startswith('/'):
            # Работа с VFS
            entries = self.vfs.list_directory(path)
            for entry in entries:
                print(entry)
        else:
            # Работа с реальной файловой системой
            try:
                actual_path = os.path.expanduser(path) if path == "~" else path
                if os.path.exists(actual_path):
                    for item in os.listdir(actual_path):
                        print(item)
                else:
                    print(f"Директория не существует: {path}")
            except Exception as e:
                print(f"Ошибка: {e}")

    def cmd_cd(self, args: List[str]) -> None:
        if not args:
            self.current_dir = "~"
        else:
            self.current_dir = args[0]
        print(f"Текущая директория: {self.current_dir}")

    def cmd_cat(self, args: List[str]) -> None:
        if not args:
            print("Usage: cat <file>")
            return

        filename = args[0]
        if filename.startswith('/'):
            # Чтение из VFS
            content = self.vfs.get_file_content(filename)
            if content is not None:
                print(content)
            else:
                print(f"Файл не найден в VFS: {filename}")
        else:
            # Чтение из реальной файловой системы
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    print(f.read())
            except Exception as e:
                print(f"Ошибка чтения файла: {e}")

    def cmd_pwd(self, args: List[str]) -> None:
        print(self.current_dir)

    def cmd_echo(self, args: List[str]) -> None:
        print(' '.join(args))

    def cmd_exit(self, args: List[str]) -> None:
        print("Завершение работы эмулятора")
        self.running = False

    def run_script(self, script_path: str) -> None:
        """Выполняет стартовый скрипт"""
        if not os.path.exists(script_path):
            print(f"Ошибка: скрипт не найден: {script_path}")
            return

        self.is_running_script = True
        print(f"Выполнение скрипта: {script_path}")
        print("-" * 40)

        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                # Пропускаем пустые строки и комментарии
                if not line or line.startswith('#'):
                    continue

                # Отображаем ввод (имитация пользовательского ввода)
                prompt = self.get_prompt()
                print(f"{prompt}{line}")

                # Выполняем команду
                parts = self.parse_arguments(line)
                if not parts:
                    continue

                command = parts[0]
                args = parts[1:] if len(parts) > 1 else []

                if not self.execute_command(command, args):
                    print(f"Ошибка в строке {line_num}: {line}")
                    break

        except Exception as e:
            print(f"Критическая ошибка выполнения скрипта: {e}")
        finally:
            self.is_running_script = False
            print("-" * 40)
            print("Завершение выполнения скрипта")

    def run(self):
        print("Добро пожаловать в эмулятор командной оболочки!")
        print("Для выхода введите 'exit'")
        print("-" * 50)

        # Если указан скрипт - выполняем его
        if self.script_path:
            self.run_script(self.script_path)
            if not self.is_running_script:
                print("Возврат в интерактивный режим...")
                print("-" * 50)

        # Интерактивный режим
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
    parser = argparse.ArgumentParser(description='Эмулятор командной оболочки с VFS')
    parser.add_argument('--vfs', type=str, help='Путь к файлу VFS (JSON)')
    parser.add_argument('--script', type=str, help='Путь к стартовому скрипту')

    args = parser.parse_args()

    shell = ShellEmulator(vfs_path=args.vfs, script_path=args.script)
    shell.run()


if __name__ == "__main__":
    main()