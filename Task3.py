from typing import Any, Callable, Iterable


class InputException(Exception):
    message = "Input error, try again"

    def __init__(self, message=None | str):
        if message:
            self.message = message

    def __str__(self):
        return self.message


class TaskException(Exception):
    def __init__(self, exc: Exception, task_name: str):
        self.exc = exc
        self.task_name = task_name

    def __str__(self):
        return f"In {self.task_name} : {self.exc.__class__} - {self.exc}"


class Task:
    separator = "---------------------------------------"
    repeat = True
    task: Callable[[dict], str]
    name = ""
    repeat_input_message = "Are you want to repeat this task? "
    input_args_message = "Send arguments"

    def __init__(
        self,
        task,
        name,
        repeat=True,
        separator=None,
        repeat_input_message=None,
        input_args_message=None,
        detail=False,
        args=None,
    ) -> None:
        if not callable(task):
            raise ValueError("task shoud be callable")

        self.task = task
        self.name = name
        self.repeat = repeat
        self.detail = detail
        self.args = args
        if separator:
            self.separator = separator
        if repeat_input_message:
            self.repeat_input_message = repeat_input_message
        if input_args_message:
            self.input_args_message = input_args_message

    def __launch_task(self, args: dict[str, Any]) -> str:
        if len(args) == 0:
            result = self.task()
        else:
            result = self.task(args)

        try:
            str(result)
        except:
            raise ValueError("Task function must always return a string")

        return result

    def __get_detail_data(self, args: dict[str, Any]) -> tuple:
        from time import time as t

        s = t()
        result = self.__launch_task(args)
        time = t() - s

        return_args = ", ".join([f"{name} - {value}" for name, value in args.items()])

        return return_args, result, time

    def get_result(self, args: dict[str, Any]) -> str:
        if self.detail:
            data = self.__get_detail_data(args)
            return f"Args - {data[0]}\nResult - {data[1]}\nTime - {data[2]} seconds"
        else:
            return f"Result - {self.__launch_task(args)}"

    def __raise_if_not_convert(self, arg: Any, type) -> Any | None:
        try:
            return type(arg)
        except:
            raise InputException(f"argument {arg} нелья конверктнуть до {type}")

    def __get_single_arg(self, arg: Iterable, args: dict[str, Any]) -> None:
        # single args looks like: [name:str,type,input_text:str]
        name, type, text = arg
        resp = input(f"{text}: ")
        args[name] = self.__raise_if_not_convert(resp, type)

    def __get_list_arg(self, arg: Iterable, args: dict[str, Any]) -> None:
        # list args looks like : [name:str,list,input_text:str,list_options:iterrable]
        # list_options : [*types*,separator:str]
        name, type, text, options = arg

        separator = options[-1]

        if not isinstance(separator, str):
            raise ValueError(f"Separator for {name} must be a string type")

        resp_list = input(f"{text} :").split(separator)
        types = options[:-1]

        if len(types) != len(resp_list):
            raise InputException("You write to many arguments")

        is_one_type = len(types) == 1
        args_list = []

        for i, s in enumerate(resp_list):
            if not is_one_type:
                type = types[i]
            args_list.append(self.__raise_if_not_convert(s, type))

        args[name] = args_list

    def get_args(self) -> dict[str, Any]:
        args = {}

        for arg in self.args:
            le = len(arg)

            if le not in (3, 4):
                raise ValueError("Len arg shoud be 3 or 4")
            if le == 3:
                self.__get_single_arg(arg, args)
            elif le == 4:
                self.__get_list_arg(arg, args)

        return args

    def show_repeat_message(self) -> bool:
        resp = input(self.repeat_input_message)
        return resp == "1"

    def run(self) -> None:
        print(self.separator)
        print(self.name)

        while True:
            try:
                args = self.get_args()
                print(self.get_result(args))
                if self.repeat and self.show_repeat_message():
                    continue
                else:
                    break

            except InputException as exc:
                print(exc.message)
                continue

            except Exception as exc:
                raise TaskException(exc, self.name)

        print(self.separator)

    def set_attrs(self, **kwargs):
        for name, value in kwargs.items():
            setattr(self, name, value)
        return self


def task(
    name: str = None,
    repeat=True,
    separator=None,
    repeat_input_message=None,
    input_args_message=None,
    detail=False,
    args=None,
) -> Callable[[Callable | Task], Task]:
    
    def wrap(task: Callable | Task):
        if len(args) != 0 and not iter(args[0]):
            args = [args]
    
    
    def wrap(task: Callable | Task):
        if callable(task):
            if name is None:
                raise ValueError("decorator on function must have name parameter")

            return Task(
                task,
                name,
                repeat,
                separator,
                repeat_input_message,
                input_args_message,
                detail,
                args,
            )

        if isinstance(task, Task):
            if name is None:
                task_name = task.name
            else:
                task_name = name

            return task.set_attrs(
                name=task_name,
                repeat=repeat,
                separator=separator,
                repeat_input_message=repeat_input_message,
                input_args_message=input_args_message,
                detail=detail,
                args=args,
            )
        else:
            raise ValueError("Decorator work with function or Task type value")

    return wrap


class TaskLauncher:
    supported_types = {"int": int, "str": str, "float": float}

    @classmethod
    def __get_correct_name(cls, raw_name: str):
        name = raw_name.replace("task_", "", 1)
        name = " ".join([c.capitalize() for c in name.split("_")])
        return name

    @classmethod
    def __reverse_correct_name(cls, name: str):
        return "_".join([x.lower() for x in name.replace(" ", "_").split("_")])

    @classmethod
    def __parse_func_name(cls, name: str, task_func):
        repeat = True
        detail = False

        name_args = name.replace("task_", "", 1).split("__")
        task_name = cls.__get_correct_name(name_args[0])
        args = [x.split("_") for x in name_args[1:]]

        single_args = []
        variable_type_args = []

        for arg in args:
            l = len(arg)
            if l == 1:
                single_args.append(arg[0])
            elif l == 2:
                variable_type_args.append(arg)
            else:
                e = "_".join(arg)
                raise ValueError(f"only two value shoub be splice by _, your {e}")

        if "notrepeat" in single_args:
            repeat = False
        if "detail" in single_args:
            detail = True

        args_for_task = []
        for var_name, str_type in variable_type_args:
            if str_type not in cls.supported_types:
                raise ValueError(f"unsupported type {type}")
            type = cls.supported_types[str_type]
            args_for_task.append([var_name, type, f"input {str_type}"])

        return Task(
            task_func, task_name, args=args_for_task, detail=detail, repeat=repeat
        )

    @classmethod
    @property
    def tasks(cls) -> dict[str, Task]:
        tasks = {}

        for name, task in cls.__dict__.items():
            if name.startswith("task_") and callable(task):
                task = cls.__parse_func_name(name, task)
                name = task.name

            elif isinstance(task, Task):
                name = task.name

            else:
                continue

            tasks[name] = task

        return tasks

    @classmethod
    def run_all(cls):
        for task in cls.tasks.values():
            task.run()

    @classmethod
    def run(cls, *names: str):
        tasks = cls.tasks
        for name in names:
            if name.find("_") != -1:
                name = cls.__get_correct_name(name)
            if name in tasks:
                tasks[name].run()
            else:
                raise KeyError(f"no task with name {name}")



class Parser:
    pass