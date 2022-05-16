import c_utils
import pandas as pd
import EntityExtract as ee
import InstrumentDict
from docx.api import Document


def extract_tables(document_path):

    document = Document(document_path)
    df = pd.DataFrame(columns=['field', 'info'])

    for table in document.tables:
        if len(table.columns) == 2:
            append_df = pd.DataFrame([[c_utils.strip(cell.text) for cell in row.cells] for row in table.rows], columns=['field', 'info'])
            df = df.append(append_df, ignore_index=True)
        else:
            continue
    df = df.set_index('field')
    return df


def parse_fields(file_path):

    instr_dict = InstrumentDict.load_instr_dict()
    df = extract_tables(file_path)

    fields = {}
    links = {}

    instr = ee.extract_instrument(df.loc['Instrument', 'info']).split(',')
    instr = tuple([c_utils.strip(i) for i in instr])

    for func, field in instr_dict[(instr)].items():
        df_field = [df.loc[i, 'info'] for i in field]
        extracted, link = func(*df_field)
        fields = c_utils.merge_dicts(fields, extracted)
        links = c_utils.merge_dicts(links, link)

    return fields, links, instr
