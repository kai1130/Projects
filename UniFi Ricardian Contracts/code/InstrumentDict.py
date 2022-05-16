import pickle
import EntityExtract as ee


def update_instr_dict():

    filepath = './instr_dict.pkl'
    instr_dict = {('debt instrument','fixed'): {
                       ee.extract_date: ['Maturity Date','Issue Date'],
                       ee.extract_nominal: ['Nominal Amount'],
                       ee.extract_interest: ['Coupon Rate']},
                  ('multiplier', 'simple'): {
                      ee.extract_tokenName: ['Token Name'],
                      ee.extract_tokenSymbol: ['Token Symbol'],
                      ee.extract_multiple: ['Multiplier'],
                  }
                 }

    dict_file = open(filepath, "wb")
    pickle.dump(instr_dict, dict_file)
    dict_file.close()


def load_instr_dict():

    filepath = './instr_dict.pkl'
    dict_file = open(filepath, "rb")
    output = pickle.load(dict_file)
    dict_file.close()
    return output


if __name__ == "__main__":
    update_instr_dict()
