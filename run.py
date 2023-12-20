from flask import Flask
from app.config import db
from app.routes import sala
from flasgger import Swagger

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:12345@localhost/salas'
swagger = Swagger(app)

# Configuração do banco de dados
db.init_app(app)

# Registrar blueprints
app.register_blueprint(sala)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
