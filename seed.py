"""
Popula o banco com dados FICTÍCIOS de demonstração.

Nenhum nome, número ou unidade aqui vem do arquivo original — foram
inventados livremente só para o sistema ter o que mostrar na primeira
execução.
"""
from datetime import date, datetime, timedelta

from app.models import Escala, Militar, Missao, OrdemServico, Pelotao, PostoServico, Unidade, agora_utc, db


def popular_dados(recriar_tabelas=True):
    """Preenche o banco com dados fictícios. Chamada pelo script de linha de
    comando (abaixo) e também pelo app factory, para autopopular bancos novos
    em produção (ex.: Postgres recém-criado no deploy)."""
    if recriar_tabelas:
        db.drop_all()
    db.create_all()

    # --- Unidades e pelotões -------------------------------------------
    bia_cs = Unidade(sigla="Bia C Sl", nome="Bateria de Comando e Serviços")
    bia_1 = Unidade(sigla="1ª Bia O Sl", nome="1ª Bateria Operacional")
    bia_2 = Unidade(sigla="2ª Bia O Sl", nome="2ª Bateria Operacional")
    db.session.add_all([bia_cs, bia_1, bia_2])
    db.session.flush()

    pel_1 = Pelotao(nome="1º Pelotão", unidade_id=bia_cs.id)
    pel_2 = Pelotao(nome="2º Pelotão", unidade_id=bia_cs.id)
    sec_sau = Pelotao(nome="Seção de Saúde", unidade_id=bia_cs.id)
    pel_1a = Pelotao(nome="1º Pelotão", unidade_id=bia_1.id)
    db.session.add_all([pel_1, pel_2, sec_sau, pel_1a])
    db.session.flush()

    # --- Postos de serviço ------------------------------------------------
    postos = [
        PostoServico(nome="Gd Paiol", tipo="Externo", contingente=75),
        PostoServico(nome="Sentinela Portão Principal", tipo="Externo", contingente=40),
        PostoServico(nome="Gd Viaturas", tipo="Externo", contingente=30),
        PostoServico(nome="Plantão Rancho", tipo="Interno", contingente=20),
        PostoServico(nome="Plantão Enfermaria", tipo="Interno", contingente=15),
        PostoServico(nome="Cabo de Dia", tipo="Interno", contingente=25),
    ]
    db.session.add_all(postos)
    db.session.flush()

    # --- Militares (fictícios) --------------------------------------------
    militares = [
        Militar(posto_grad="1º Ten", numero="0015", nome_guerra="Rodrigues", nome_completo="João Rodrigues",
                cargo="Comandante de Pelotão", unidade_id=bia_cs.id, pelotao_id=pel_1.id,
                username="rodrigues", is_admin=True),
        Militar(posto_grad="2º Sgt", numero="0102", nome_guerra="Almeida", nome_completo="Marcos Almeida",
                cargo="Sargenteante", unidade_id=bia_cs.id, pelotao_id=pel_1.id, username="almeida"),
        Militar(posto_grad="3º Sgt", numero="0187", nome_guerra="Pereira", nome_completo="Carlos Pereira",
                unidade_id=bia_cs.id, pelotao_id=pel_2.id, username="pereira"),
        Militar(posto_grad="Cb EP", numero="0298", nome_guerra="Santos", nome_completo="Bruno Santos",
                unidade_id=bia_cs.id, pelotao_id=pel_2.id, username="santos"),
        Militar(posto_grad="Cb EP", numero="0355", nome_guerra="Ferreira", nome_completo="Diego Ferreira",
                unidade_id=bia_1.id, pelotao_id=pel_1a.id, username="ferreira"),
        Militar(posto_grad="Sd EP", numero="0330", nome_guerra="Bastos", nome_completo="Bastos",
                unidade_id=bia_cs.id, pelotao_id=pel_1.id, username="bastos"),
        Militar(posto_grad="Sd EP", numero="0451", nome_guerra="Silva", nome_completo="Gabriel Silva",
                unidade_id=bia_cs.id, pelotao_id=pel_1.id, username="silva"),
        Militar(posto_grad="Sd EP", numero="0512", nome_guerra="Oliveira", nome_completo="Lucas Oliveira",
                unidade_id=bia_cs.id, pelotao_id=pel_2.id, username="oliveira"),
        Militar(posto_grad="Sd EP", numero="0630", nome_guerra="Costa", nome_completo="Rafael Costa",
                unidade_id=bia_1.id, pelotao_id=pel_1a.id, username="costa"),
        Militar(posto_grad="Sd EV", numero="0044", nome_guerra="Souza", nome_completo="Pedro Souza",
                unidade_id=bia_2.id, username="souza"),
        Militar(posto_grad="Sd EP", numero="0721", nome_guerra="Lima", nome_completo="Thiago Lima",
                unidade_id=bia_2.id, username="lima"),
    ]
    for m in militares:
        m.set_password("123456")
    db.session.add_all(militares)
    db.session.flush()

    por_username = {m.username: m for m in militares}

    # --- Escalas de hoje ----------------------------------------------------
    hoje = date.today()
    agora = agora_utc()

    escalas = [
        Escala(data=hoje, posto_id=postos[0].id, militar_id=por_username["silva"].id,
               responsavel_id=por_username["almeida"].id, notificado_em=agora - timedelta(hours=3),
               confirmado_em=agora - timedelta(hours=2)),
        Escala(data=hoje, posto_id=postos[1].id, militar_id=por_username["oliveira"].id,
               responsavel_id=por_username["almeida"].id, notificado_em=agora - timedelta(hours=3)),
        Escala(data=hoje, posto_id=postos[2].id, militar_id=por_username["bastos"].id,
               responsavel_id=por_username["pereira"].id, notificado_em=agora - timedelta(hours=1),
               confirmado_em=agora - timedelta(minutes=40)),
        Escala(data=hoje, posto_id=postos[3].id, militar_id=por_username["costa"].id,
               responsavel_id=por_username["ferreira"].id),
        Escala(data=hoje, posto_id=postos[5].id, militar_id=por_username["souza"].id,
               responsavel_id=por_username["pereira"].id, notificado_em=agora - timedelta(hours=2)),
    ]
    db.session.add_all(escalas)

    db.session.add(Missao(data=hoje, local="Comando da Guarnição", militar_id=por_username["lima"].id))

    # --- Ordens de Serviço -------------------------------------------------
    db.session.add(OrdemServico(
        numero="158", data=hoje, assunto="Instrução de tiro — 3º BI",
        conteudo=(
            "1. A instrução de tiro programada para amanhã foi remarcada para "
            "a próxima segunda-feira, mesmo horário.\n\n"
            "2. Os pelotões escalados devem se apresentar ao paiol às 07h30 "
            "para verificação de material."
        ),
        publicado_por_id=por_username["rodrigues"].id,
    ))
    db.session.add(OrdemServico(
        numero="157", data=hoje - timedelta(days=1), assunto="Manutenção do sistema de água",
        conteudo="1. O fornecimento de água será interrompido das 09h às 11h para reparo na caixa d'água principal.",
        publicado_por_id=por_username["rodrigues"].id,
    ))

    db.session.commit()
    print("Banco populado com dados fictícios.")
    print(f"Militares cadastrados: {len(militares)}")
    print("Login de demonstração: usuário 'bastos', senha '123456'")


if __name__ == "__main__":
    from app import create_app

    app = create_app(auto_seed=False)
    with app.app_context():
        popular_dados()
