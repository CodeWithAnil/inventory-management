from app import db
from sqlalchemy.orm import relationship



class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    serial_number = db.Column(db.String(50), unique=True, nullable=False)
    bill_number = db.Column(db.String(50), unique=True, nullable=False)
    date_of_purchase = db.Column(db.Date, nullable=False)
    warranty = db.Column(db.String(50), nullable=True)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    assigned_to = relationship('User')

    def __repr__(self):
        return f"Item(name='{self.name}', serial_number='{self.serial_number}', bill_number='{self.bill_number}')"
