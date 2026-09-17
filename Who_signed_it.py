from supp_adel import ConnectionFactory
from datetime import timedelta

cf = ConnectionFactory()

connect_organization = cf.get_connection('organization')
table_organization = connect_organization.get_table('user')

databases = [ 'db_prod_1', 'db_prod_2']

# Ввод номеров процедур
procedur_list = [proc.strip() for proc in input("Введи номер процедуры через запятую: ").strip().split(',') if
                 proc.strip()]

for a_procedur in procedur_list:
    print("=" * 80)

    # Поиск процедуры в базах
    target_connection = None
    for db_name in databases:
        connection = cf.get_connection(db_name)
        procedures_table = connection.get_table('procedures')
        with connection.get_session() as sess:
            if sess.query(procedures_table.id).filter(
                    procedures_table.registrationNumber == a_procedur,
                    procedures_table.actualId.is_(None)
            ).first():
                target_connection = connection
                break

    if not target_connection:
        print(f"Процедура {a_procedur} не найдена в базах данных")
        print("-" * 80)
        continue

    procedures_table = target_connection.get_table('procedures')
    lot_table = target_connection.get_table('lot')
    protocol_table = target_connection.get_table('protocol')
    signature_table = target_connection.get_table('signature')

    # Основной запрос
    with target_connection.get_session() as sess:
        result = sess.query(
            protocol_table.id,
            protocol_table.publishDateTime,
            signature_table.userId
        ).join(
            lot_table,
            protocol_table.lotId == lot_table.id
        ).join(
            procedures_table,
            lot_table.procedureId == procedures_table.id
        ).join(
            signature_table,
            protocol_table.signatureId == signature_table.id
        ).filter(
            procedures_table.registrationNumber == a_procedur,
            protocol_table.discriminator.like('%final%'),
            procedures_table.actualId.is_(None)
        ).first()

    if not result:
        print(f"Нет протоколов финальных ПОСМОТРИ рукамив БД {a_procedur}")
        print("-" * 80)
        continue

    protocol_id, publish_date, sig = result

    # Получаем externalId пользователя
    with connect_organization.get_session() as sess:
        user = sess.query(table_organization.externalId).filter(
            table_organization.id == sig
        ).first()

    if not user:
        print(f"Нет пользователя в organization БД для процедуры {a_procedur}")
        print("-" * 80)
        continue

    id_user = user.externalId

    # Дата
    start_data = publish_date - timedelta(minutes=2)
    end_data = publish_date + timedelta(minutes=2)
    start_str = start_data.strftime("%d.%m.%Y %H:%M")  # форматируем без секунд
    end_str = end_data.strftime("%d.%m.%Y %H:%M")  # форматируем без секунд

    uri = f'https://example.com/httpAction/user/{id_user}/?uri={protocol_id}&dateTime-from={start_str.replace(" ", "%20").replace(":", "%3A")}&dateTime-to={end_str.replace(" ", "%20").replace(":", "%3A")}&'
    print(uri)
print("=" * 80)
print("Обработка всех процедур завершена!")