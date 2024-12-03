from . import db


class Job(db.Model):
    __tablename__ = 'jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    salary = db.Column(db.Float)
    currency = db.Column(db.String)
    experience = db.Column(db.Float)
    link = db.Column(db.String, unique=True)
    date = db.Column(db.String)

    skills = db.relationship('Skill', back_populates='job')


class Skill(db.Model):
    __tablename__ = 'skills'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'))
    counter = db.Column(db.Integer)

    job = db.relationship('Job', back_populates='skills')


class SkillsList(db.Model):
    __tablename__ = "skills_list"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)


class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, unique=True, nullable=False)

    subscriptions = db.relationship('Subscription', back_populates='user')


class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    room_name = db.Column(db.String, nullable=False)  # The room or topic name
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    user = db.relationship('User', back_populates='subscriptions')