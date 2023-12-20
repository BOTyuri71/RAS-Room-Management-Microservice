from flask import Blueprint, jsonify, request, current_app
from flasgger import Swagger
from flasgger.utils import swag_from
from .models import Sala, Prova, Sala_Prova_Link, db
from datetime import datetime, timedelta
import pandas as pd

sala = Blueprint('sala', __name__)

@sala.route('/adicionar-sala', methods=['POST'])
@swag_from('swagger/adicionar_sala.yaml') 
def adicionar_sala():
    # Verifica se a requisição é do tipo POST
    if request.method == 'POST':
        # Obtém os dados JSON da requisição
        dados = request.json

        # Cria uma nova sala com os dados recebidos
        nova_sala = Sala(nome=dados['nome'], capacidade=dados['capacidade'])

        # Adiciona a nova sala ao banco de dados
        db.session.add(nova_sala)
        db.session.commit()

        return jsonify({"mensagem": "Sala adicionada com sucesso!"})

    return jsonify({"mensagem": "Requisição inválida."})

@sala.route('/sala/<int:sala_id>', methods=['GET'])
def get_sala(sala_id):
    sala = Sala.query.get(sala_id)

    if sala:
        # Serializa a sala para um formato JSON e a retorna
        sala_json = {
            'idSala': sala.idSala,
            'nome': sala.nome,
            'capacidade': sala.capacidade
        }
        return jsonify(sala_json)
    else:
        # Se a sala com o ID especificado não for encontrada, retorna uma resposta de erro
        return jsonify({'mensagem': 'Sala não encontrada'}), 404

@sala.route('/remover-sala/<int:sala_id>', methods=['DELETE'])
def remover_sala(sala_id):
    sala = Sala.query.get(sala_id)

    if sala:
        # Salva o ID da sala antes de ser removida
        id_sala_removida = sala.idSala

        # Remove a sala do banco de dados
        db.session.delete(sala)
        db.session.commit()

        # Retorna um JSON com o ID da sala removida
        return jsonify({'mensagem': 'Sala removida com sucesso', 'idSala': id_sala_removida})
    else:
        # Se a sala com o ID especificado não for encontrada, retorna uma resposta de erro
        return jsonify({'mensagem': 'Sala não encontrada'}), 404


@sala.route('/get-all-salas', methods=['GET'])
def obter_todas_salas():
    salas = Sala.query.all()

    # Serializa todas as salas para um formato JSON e as retorna
    salas_json = [{'idSala': sala.idSala, 'nome': sala.nome, 'capacidade': sala.capacidade} for sala in salas]
    return jsonify(salas_json)        

@sala.route('/set-salas', methods=['POST'])
def set_salas():
    # Verifica se a requisição é do tipo POST e contém dados JSON
    if request.method == 'POST' and request.is_json:
        dados = request.json

        # Extrai os dados necessários da solicitação JSON
        id_prova = dados.get('idProva')
        data = dados.get('data')
        hora = dados.get('hora')
        duracao = dados.get('duracao')
        tempo_admissao = dados.get('tempo_admissao')
        salas = dados.get('salas')

        # Cria uma nova instância de Prova
        nova_prova = Prova(idProva=id_prova, data=data, hora=hora, duracao=duracao, tempo_admissao=tempo_admissao)

        # Associa as salas à nova prova
        for sala in salas:
            idSala = sala.get('idSala')
            sala_prova = Sala_Prova_Link(idSala=idSala, idProva=nova_prova.idProva)
            db.session.add(sala_prova)

        # Adiciona a nova prova ao banco de dados
        db.session.add(nova_prova)
        db.session.commit()

        return jsonify({"mensagem": "Prova e salas associadas com sucesso!"})

    return jsonify({"mensagem": "Requisição inválida."})   

@sala.route('/get-salas/<int:id_prova>', methods=['GET'])
def get_salas(id_prova):
    # Consulta as salas associadas à prova específica
    salas_associadas = Sala_Prova_Link.query.filter_by(idProva=id_prova).all()

    if not salas_associadas:
        return jsonify({"mensagem": "Prova não encontrada ou sem salas associadas"}), 404

    # Obtém os detalhes das salas associadas
    detalhes_salas = []
    for associacao in salas_associadas:
        sala = Sala.query.get(associacao.idSala)
        if sala:
            detalhes_sala = {
                "idSala": sala.idSala,
                "nome": sala.nome,
                "capacidade": sala.capacidade
            }
            detalhes_salas.append(detalhes_sala)

    return jsonify(detalhes_salas)    

def sala_disponivel_para_prova(idSala, idProva):
    # Obter informações sobre a prova
    prova = Prova.query.get(idProva)

    # Obter todas as provas associadas à sala
    provas_associadas = db.session.query(Prova).join(Sala_Prova_Link).filter_by(idSala=idSala).all()

    # Calcular horários importantes da nova prova
    hora_inicio_nova_prova = datetime.combine(prova.data, prova.hora)
    hora_termino_nova_prova = hora_inicio_nova_prova + timedelta(minutes=prova.duracao + prova.tempo_admissao)

    # Verificar se há alguma prova que interfere com a nova prova
    for prova_associada in provas_associadas:
        hora_inicio_prova_associada = datetime.combine(prova_associada.data, prova_associada.hora)
        hora_termino_prova_associada = hora_inicio_prova_associada + timedelta(
            minutes=prova_associada.duracao + prova_associada.tempo_admissao
        )

        # Verificar se há sobreposição com a nova prova
        if (
            (hora_termino_prova_associada > hora_inicio_nova_prova and hora_termino_prova_associada <= hora_termino_nova_prova) or
            (hora_inicio_prova_associada >= hora_inicio_nova_prova and hora_inicio_prova_associada < hora_termino_nova_prova)
        ):
            return False  # Sala indisponível

    return True  # Sala disponível

@sala.route('/valida-disp', methods=['POST'])
def verificar_disponibilidade():
    dados = request.json

    # Verificar se todos os parâmetros necessários estão presentes
    if not all(key in dados for key in ['idSala', 'idProva']):
        return jsonify({"mensagem": "Parâmetros incompletos"}), 400

    idSala = dados['idSala']
    idProva = dados['idProva']

    # Verificar se a sala está disponível para a prova
    disponibilidade = sala_disponivel_para_prova(idSala, idProva)

    return jsonify({"disponibilidade": disponibilidade})

def validar_csv(file_path):
    try:
        # Tentar ler o CSV usando pandas
        df = pd.read_csv(file_path)

        # Verificar se o CSV possui as colunas esperadas
        if 'nome' not in df.columns or 'capacidade' not in df.columns:
            return False, "O arquivo CSV deve conter colunas 'nome' e 'capacidade'."

        return True, df

    except Exception as e:
        return False, str(e)
        
@sala.route('/valida-ficheiro', methods=['POST'])
def adicionar_salas_csv():
    # Verificar se o pedido contém um arquivo
    if 'file' not in request.files:
        return jsonify({"mensagem": "Nenhum arquivo enviado"}), 400

    file = request.files['file']

    # Verificar se o arquivo tem uma extensão válida
    if file.filename == '' or not file.filename.lower().endswith(('.csv')):
        return jsonify({"mensagem": "Formato de arquivo inválido. Deve ser um arquivo CSV."}), 400

    # Salvar o arquivo temporariamente
    file_path = 'temp.csv'
    file.save(file_path)

    # Validar o CSV
    sucesso, dados_csv = validar_csv(file_path)

    if not sucesso:
        return jsonify({"mensagem": dados_csv}), 400

    # Adicionar salas ao banco de dados
    salas_adicionadas = 0
    for _, sala_info in dados_csv.iterrows():
        nome = sala_info['nome']
        capacidade = sala_info['capacidade']

        # Verificar se a sala já existe pelo nome
        if Sala.query.filter_by(nome=nome).first() is None:
            nova_sala = Sala(nome=nome, capacidade=capacidade)
            db.session.add(nova_sala)
            salas_adicionadas += 1

    db.session.commit()

    return jsonify({"mensagem": f"Ficheiro lido com sucesso e {salas_adicionadas} salas adicionadas."})