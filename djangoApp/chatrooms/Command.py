from abc import ABC, abstractmethod
from . import JsonConverter
from .models import *
from .Task import Task
import json
from datetime import datetime
from django.contrib.auth import get_user_model
User = get_user_model()


class Command(ABC):
    @abstractmethod
    async def execute(self):
        pass


class FetchCommand(Command):
    def __init__(self, consumer, data):
        self.consumer = consumer
        self.data = data

    async def execute(self):
        class_room = self.data['room_name']
        messages = Message.last_10_messages(class_room)
        jsonConverter = JsonConverter.JsonConverterContext(JsonConverter.MessageToJsonConverter())
        print(messages)
        content = {
            'command': 'messages',
            'messages': jsonConverter.convert_multiple(messages)
        }

        await self.consumer.send_chat_message_fetch(content)


class FetchTasks(Command):
    def __init__(self, consumer, data):
        self.consumer = consumer
        self.data = data

    async def execute(self):
        username = self.data['username']
        class_room = self.data['room_name']
        tasks = Task_model.last_10_tasks(class_room)
        answers = Answer.last_answers(class_room, username)
        print(len(tasks))
        jsonConverter = JsonConverter.JsonConverterContext(JsonConverter.TaskToJsonConverter())
        answerToJson = JsonConverter.JsonConverterContext(JsonConverter.AnswerToJson())
        content = {
            'command': 'tasks',
            'tasks': jsonConverter.convert_multiple(tasks),
            'answers': answerToJson.convert_multiple(answers)
        }

        await self.consumer.send_chat_message_fetch(content)


class GetTask(Command):
    def __init__(self, consumer, data):
        self.consumer = consumer
        self.data = data

    async def execute(self):

        id = self.data['id']
        classroom = self.data['classroom_name']
        author = self.data['username']
        tasks = Task_model.objects.all().filter(content_id=id,classroom_name=classroom)
        answer = Answer.objects.all().filter(task_id = id, classroom_token = classroom, author_of_answer = author)
        l : list[json]
        l = []
        print(len(answer))
        if(len(answer) > 0):
            for task in tasks:
                l.append({
                'type' : 'solved_task',
                'author': task.author.username,
                'content_problem': task.content_problem,
                'content_answer': task.content_answer,
                'id': task.content_id,
                'timestamp': str(task.timestamp),
                'classroom_name': task.classroom_name,
                'user_points': answer[0].points,
                'max_points': task.points,
                'task_name': task.task_name,
                'user_answer': answer[0].answer,

            })
            await self.consumer.sendTaskWithUserAnswer({'task': l[0]})
        else:
            for task in tasks:
                l.append({
                    'type': 'solved_task',
                    'author': task.author.username,
                    'content_problem': task.content_problem,
                    'content_answer': task.content_answer,
                    'id': task.content_id,
                    'timestamp': str(task.timestamp),
                    'classroom_name': task.classroom_name,
                    'points': task.points,
                    'task_name': task.task_name,
                    'user_answer': None,

                })
            await self.consumer.sendTask({ 'task' : l[0]})


class NewMessageCommand(Command):
    def __init__(self, consumer, data):
        self.consumer = consumer
        self.data = data

    async def execute(self):
        print('new message')
        author = self.data['author']
        message_ = self.data['message']
        classroom = self.data['classroom_name']
        user = User.objects.get(username=author)
        dt = datetime.now()
        ts = datetime.timestamp(dt)
        message = Message.objects.create(author=user, content=message_,classroom_name = classroom)
        message.save()
        jsonConverter = JsonConverter.JsonConverterContext(JsonConverter.MessageToJsonConverter())

        content = {
            'command': 'new_message',
            'message': jsonConverter.convert_single(message)
        }
        print(content)
        await self.consumer.send_chat_message(content)


class NewTaskCommand(Command):
    def __init__(self, consumer, data):
        self.consumer = consumer
        self.data = data

    async def execute(self):
        print(self.data)
        author = self.data['author']
        answear = self.data['answer']
        print('NewTaskCommand')
        content = self.data['content']
        classroom = self.data['classroom_name']
        points = self.data['points']
        task_name = self.data['task_name']
        user = User.objects.get(username=author)
        tasks = Task_model.last_10_tasks(classroom)
        print(tasks)
        if(len(tasks)==0):
            id = 1
        else:
            max : int = tasks[0].content_id
            for i in tasks:
                if i.content_id > max:
                    max = i.content_id
            id = 1 + max

        task = Task(content, answear, id,classroom,points,task_name)
        print(id)
        self.consumer.addTaskToListOfTasks(task)
        print(task)
        task_model = Task_model.objects.create(author=user, content_problem=task.task, content_answer=task.answear, content_id=task.id,classroom_name = classroom,points =points,task_name= task.task_name )
        jsonConverter = JsonConverter.JsonConverterContext(JsonConverter.TaskToJsonConverter())

        content = {
            'command': 'new_task',
            'task': jsonConverter.convert_single(task_model)
        }
        await self.consumer.sendTask(content)


class GenerateInviteLink(Command):
    def __init__(self, consumer, data):
        self.consumer = consumer
        self.data = data

    async def execute(self):
        token = self.data['token']
        chatroom = Classroom.objects.get(token=token)
        invite_code = chatroom.generate_invite()
        await self.consumer.send(text_data=json.dumps({
            'type': 'code_generation',
            'invite_code': invite_code,
        }))


class CheckAnswerCommand(Command):
    def __init__(self, consumer, data):
        self.consumer = consumer
        self.data = data

    async def execute(self):
        print('CheckAnswearCommand')
        answer_user = self.data['answer_user']

        author = self.data['username']
        classroom_token = self.data['classroom_name']
        task_id = self.data['id']

        answer = Answer.objects.all().filter(task_id=task_id, author_of_answer=author, classroom_token=classroom_token)
        task = Task_model.objects.all().filter(classroom_name=classroom_token, content_id=task_id)

        if answer[0].answer==task[0].content_answer:
            print(answer[0].answer + task[0].content_answer)
            Answer.objects.all().filter(task_id=task_id, author_of_answer=author, classroom_token=classroom_token).update(points = task[0].points)

            await self.consumer.send(text_data=json.dumps({
                'type': 'correct_answer',
                'task_id': task_id,
                'classroom_name': classroom_token,
                'author_of_answer': author,
                'points': answer[0].points
            }))
        else:
            Answer.objects.all().filter(task_id=task_id, author_of_answer=author,
                                        classroom_token=classroom_token).update(points=0)
            await self.consumer.send(text_data=json.dumps({
                'type': 'incorrect_answer',
                'task_id': task_id,
                'classroom_name': classroom_token,
                'author_of_answer': author,
                'points': answer[0].points
            }))


class SaveAnswerCommand(Command):
    def __init__(self, consumer, data):
        self.consumer = consumer
        self.data = data

    async def execute(self):
        print('SaveAnswearCommand')
        answer_user = self.data['user_ans']

        author = self.data['username']
        classroom_token = self.data['classroom_name']

        id = self.data['id']
        answer = Answer.objects.create(author_of_answer=author, answer=answer_user, classroom_token=classroom_token, points=0, task_id=id)


class GetUsersAnswers(Command):
    def __init__(self, consumer, data):
        self.consumer = consumer
        self.data = data

    async def execute(self):
        print('GetUsersAnswers')
        id = self.data['id']
        classroom_token = self.data['classroom_name']
        answers = Answer.objects.all().filter(task_id=id, classroom_token=classroom_token)
        jsonConverter = JsonConverter.JsonConverterContext(JsonConverter.TaskToJsonConverter())
        answerToJson = JsonConverter.JsonConverterContext(JsonConverter.AnswerToJson())
        print('Len of answers' + str(len(answers)))
        content = {
            'type': 'answers',
            'answers': answerToJson.convert_multiple(answers)
        }
        await self.consumer.send_user_answers((content))


class ChangeScoreCommand(Command):
    def __init__(self, consumer, data):
        self.consumer = consumer
        self.data = data

    async def execute(self):
        print('ChangeScoreCommand')
        id = self.data['id']
        classroom_token = self.data['classroom_name']
        username = self.data['username']
        new_points = self.data['points']
        Answer.objects.all().filter(task_id=id, classroom_token=classroom_token, author_of_answer = username).update(points=new_points)


class CreateQuizTaskCommand(Command):
    def __init__(self, consumer, data):
        self.consumer = consumer
        self.data = data

    async def execute(self):
        print(self.data)
        tasks = self.data['tasks']
        print(tasks)
        classname = self.data['classroom_name']
        quiz_name = self.data['quiz_name']
        quizzes = Quiz.last_quizzes(classname)
        print(classname)
        if len(quizzes)==0:
            quiz_id = 1
        else:
            max: int = quizzes[0].quiz_id
            for i in quizzes:
                if i.quiz_id > max:
                    max = i.quiz_id
            quiz_id = 1 + max
        quiz = Quiz.objects.create(quiz_id=quiz_id, num_of_questions = len(tasks), classname = classname, quiz_name = quiz_name)
        for task in tasks:
            quiz_task = QuizTask.objects.create(quiz_id = quiz_id, correct_answer = task['correct_answer'], problem=task['task_content'], classname = classname)


class FetchQuizzes(Command):
    def __init__(self, consumer, data):
        self.consumer = consumer
        self.data = data

    async def execute(self):
        classname = self.data['room_name']
        quizzes = Quiz.objects.filter(classname = classname)
        jsonConverter = JsonConverter.JsonConverterContext(JsonConverter.QuizToJson())
        content = {
            'command': 'quizzes',
            'quizzes': jsonConverter.convert_multiple(quizzes)
        }

        await self.consumer.send(text_data=json.dumps(content))
class GetQuiz(Command):
    def __init__(self, consumer, data):
        self.consumer = consumer
        self.data = data

    async def execute(self):
        quiz_id = self.data['quiz_id']
        classroom = self.data['classroom_name']
        quizTask = QuizTask.objects.filter(classname = classroom, quiz_id = quiz_id)
        author = self.data['username']
        user = User.objects.get(username=author)

        userQuizResult = QuizAnswer.objects.filter(classname = classroom, quiz_id = quiz_id, author = user)
        jsonConverter = JsonConverter.JsonConverterContext(JsonConverter.QuizTaskToJson())
        quizAnswerjsonConverter = JsonConverter.JsonConverterContext(JsonConverter.QuizTaskToJson())
        jsonQuizTask = jsonConverter.convert_multiple(quizTask)
        jsonQuizAnswer =quizAnswerjsonConverter.convert_multiple(userQuizResult)
        await self.consumer.send(text_data=json.dumps({'quiz' : jsonQuizTask,
                                                       'quiz_answer': jsonQuizAnswer}))

class SaveQuizAnswer(Command):
    def __init__(self, consumer, data):
        self.consumer = consumer
        self.data = data

    async def execute(self):
        print(SaveQuizAnswer)
        quiz_id = self.data['quiz_id']
        classroom_name = self.data['classroom_name']
        user_points = self.data['user_points']
        max_points = self.data['max_points']
        username = self.data['username']
        user = User.objects.get(username=username)
        QuizAnswer.objects.create(quiz_id=quiz_id, classname=classroom_name, author = user,
                              max_points=max_points, points = user_points)