import os
import pandas as pd


from SWG_utils import create_target_pos_extract_csv, output_target_pos_extract_csv
from add_social_info_to_csv import add_social_info_to_extracts


def create_target_pos_extract(extract_path, clause_extract_path, target_pos):
    if not os.path.exists(extract_path):  # if the csv does not exist, create the csv
        create_target_pos_extract_csv(extract_path)
    # input the clause extract
    clause_df = pd.read_csv(clause_extract_path, header=0, encoding='utf-8')
    for index, row in clause_df.iterrows():
        if any(pos.startswith(target_pos) for pos in row['POS'].split()):
            pos_list = row['POS'].split()
            target_indices = [i for i, pos in enumerate(pos_list) if pos.startswith(target_pos)]
            swg_list = row['SWG'].split()
            print(swg_list)
            print(target_indices)
            print(pos_list) # TODO: pos list and swg list mismatch. Rerun clause extract,
            if target_indices:
                for target_index in target_indices:
                    before_clause = clause_df.at[index - 1, 'SWG'] if index - 1 >= 0 else ""
                    before_clause_pos = clause_df.at[index - 1, 'POS'] if index - 1 >= 0 else ""
                    before_word = swg_list[target_index - 1] if target_index - 1 >= 0 else ""
                    before_word_pos = pos_list[target_index - 1] if target_index - 1 >= 0 else ""
                    target_word = swg_list[target_index]
                    target_word_pos = pos_list[target_index]
                    after_word = swg_list[target_index + 1] if target_index + 1 < len(swg_list) else ""
                    after_word_pos = pos_list[target_index + 1] if target_index + 1 < len(pos_list) else ""
                    after_clause = clause_df.at[index + 1, 'SWG'] if index + 1 < len(clause_df) else ""
                    after_clause_pos = clause_df.at[index + 1, 'POS'] if index + 1 < len(clause_df) else ""

                    output_target_pos_extract_csv(extract_path,row['trans_id'], before_clause, before_clause_pos,
                              before_word, before_word_pos, target_word, target_word_pos, after_word, after_word_pos,
                                after_clause, after_clause_pos)


if __name__ == '__main__':
    working_directory = "/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/"
    target_pos = 'ADJ'
    speaker_groups = ['trend'] # 'panel',
    speaker_file_date = "30may2021"  # format:ddMMMyyyy
    extract_type =  target_pos
    types = 'noSocialInfo' + '.csv'

    date = '20240516'
    for speaker_type in speaker_groups:
        extract_path = working_directory + speaker_type +"/extracts/SWG_" + speaker_type + "_" + target_pos +"_" + date + types
        clause_extract_path = working_directory + speaker_type + "/extracts/SWG_" + speaker_type + "_" + "clauses" + "_" + date + types
        # if want to use other extract, change the path here
        create_target_pos_extract(extract_path, clause_extract_path, target_pos)
        print("Target POS extract created successfully!")
        speaker_file_path = working_directory + speaker_type + "/" + 'SWG_' + speaker_type + '_speakers_' + speaker_file_date + '.csv'  # need to change in case date changes
        extract_output_path = working_directory + speaker_type + "/extracts/" + 'SWG_' + speaker_type + '_' + extract_type + '_' + date + '.csv'
        add_social_info_to_extracts(extract_path, speaker_file_path, extract_output_path)
        print("Social info added to extract successfully!")