from AlgoLawBackEnd.models import DBReader, Divider

db_reader = DBReader()
judge_divider = Divider(db_reader.judges, db_reader.cases)
