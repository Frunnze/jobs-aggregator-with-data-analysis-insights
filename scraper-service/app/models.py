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