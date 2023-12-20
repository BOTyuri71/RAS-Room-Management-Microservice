from .config import db

class Sala(db.Model):
    __tablename__ = 'Sala'

    idSala = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    capacidade = db.Column(db.Integer, nullable=False)

class Prova(db.Model):
    __tablename__ = 'Prova'

    idProva = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False)
    hora = db.Column(db.Time, nullable=False)
    duracao = db.Column(db.Integer, nullable=False)
    tempo_admissao = db.Column(db.Integer, nullable=False)

class Sala_Prova_Link(db.Model):
    __tablename__ = 'Sala_Prova_Link'

    idSalaProva = db.Column(db.Integer, primary_key=True)
    idSala = db.Column(db.Integer, db.ForeignKey('Sala.idSala'))
    idProva = db.Column(db.Integer, db.ForeignKey('Prova.idProva'))