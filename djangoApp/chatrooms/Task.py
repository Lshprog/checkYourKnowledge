class Task:
    task : str = None
    answear : str = None
    timestamp = None
    points : int = None
    id : int = None
    classroom : str = None
    def __init__(self,task : str, answear : str,id_ : int,classroom_ : str,points : int):
        self.task = task
        self.answear = answear
        self.points = points
        self.id = id_
        self.classroom = classroom_



