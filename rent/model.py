from contextlib import contextmanager
from datetime import datetime
from smtplib import SMTP

import bcrypt
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, create_engine, or_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from rent.ui_methods import format_cents

Base = declarative_base()

Session = sessionmaker()

class User(Base):
    __tablename__ = 'users'

    username = Column(String, primary_key=True)
    salt = Column(String)
    password_hash = Column(String)

class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True)
    date = Column(DateTime)
    from_user = Column(String, ForeignKey('users.username'))
    to_user = Column(String, ForeignKey('users.username'))
    amount = Column(Integer)
    settled = Column(Boolean)

def safe_equals(a, b):
    if len(a) != len(b):
        return False
    result = True
    for i in range(len(a)):
        result = result and a[i] == b[i]
    return result

class RentModel(object):
    def __init__(self, db):
        self.db = create_engine(db)

    def authenticate_user(self, session, username, password):
        entry = session.query(User).get(username)
        if entry is None:
            return False
        test_hash = bcrypt.hashpw(password, entry.salt)
        return safe_equals(test_hash, entry.password_hash)

    def create_transaction(self, session, from_user, to_user, amount):
        date = datetime.now()
        txn = Transaction(date=date,
                          from_user=from_user,
                          to_user=to_user,
                          amount=amount,
                          settled=False)
        session.add(txn)
        self.send_mail(from_user, [to_user], '''
Subject: %s sent you %s <eom>

''' % (from_user, format_cents(None, amount)))

    def create_user(self, session, username, password):
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password, salt)
        user = User(username=username, salt=salt, password_hash=password_hash)
        session.add(user)

    def get_recent_transactions(self, session, username):
        return session.query(Transaction).filter(or_(Transaction.from_user == username,
                                                     Transaction.to_user == username))

    def send_mail(self, from_user, to_user, message):
        try:
            smtp = SMTP()
            smtp.connect()
            smtp.sendmail(from_user, [to_user], message)
            smtp.quit()
        except Exception:
            # Not worth rolling back a transaction for this
            pass

    @contextmanager
    def session(self):
        session = Session(bind=self.db)
        try:
            yield session
        except:
            session.rollback()
            raise
        else:
            session.commit()
