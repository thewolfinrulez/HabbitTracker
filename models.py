from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table, Text, text, Float, select
from db_controller import db
from datetime import datetime


class TUser(db.Model):
    __tablename__ = 't_user'

    u_id = Column(Integer, primary_key=True)
    u_username = Column(String(255), nullable=False, unique=True, index=True)
    u_name = Column(String(255))
    u_email = Column(String(255))
    u_lastname = Column(String(255))
    u_created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    u_score = Column(Integer)

    def as_obj(self):
        obj = {
            "id": self.u_id,
            "name": self.u_name,
            "username": self.u_username,
            "email": self.u_email,
            "lastname": self.u_lastname,
            "score": self.u_score,
            "created_at": str(self.u_created_at)
        }
        return obj


class TGroup(db.Model):
    __tablename__ = 't_group'

    g_id = Column(Integer, primary_key=True)
    g_name = Column(String(255))
    g_owner_id = Column(ForeignKey('t_user.u_id'), nullable=False)
    g_created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))

    def as_obj(self):
        obj = {
            "id": self.g_id,
            "name": self.g_name,
            "created_at": str(self.g_created_at)
        }
        return obj


class TGroupUser(db.Model):
    __tablename__ = 't_group_user'

    gu_id = Column(Integer, primary_key=True)
    gu_group_id = Column(ForeignKey('t_group.g_id'), nullable=False)
    gu_user_id = Column(ForeignKey('t_user.u_id'), nullable=False)
    gu_created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    gu_score = Column(Integer)

    def as_obj(self):
        user = TUser.query.filter(TUser.u_id == self.gu_user_id).first()
        obj = {
            "id": self.gu_id,
            "username": user.u_username,
            "group_id": self.gu_group_id,
            "score": self.gu_score,
            "created_at": str(self.gu_created_at)
        }
        return obj


class TTask(db.Model):
    __tablename__ = 't_task'

    t_id = Column(Integer, primary_key=True)
    t_name = Column(String(255))
    t_group_id = Column(ForeignKey('t_group.g_id'), nullable=False)
    t_score_amount = Column(Integer)
    t_created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))

    def as_obj(self):
        group = TGroup.query.filter(TGroup.g_id == self.t_group_id).first()
        obj = {
            "id": self.t_id,
            "score_amount": self.t_score_amount,
            "name": self.t_name,
            "group_id": self.t_group_id,
            "group_name": group.g_name,
            "created_at": str(self.t_created_at)
        }
        return obj
