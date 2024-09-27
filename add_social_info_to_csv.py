import pandas


def add_social_info_to_extracts(extract_input_path, speaker_file_path, extract_output_path,
                                unmatched_extract_output_path='unmatched_extract_output_file.csv',
                                unmatched_social_info_output_path='unmatched_social_info_output_file.csv',
                                is_phones_extract=False):
    df_extract = pandas.read_csv(
        extract_input_path, encoding='utf-8-sig', header=0)
    if "phone" in extract_input_path or "formant" in extract_input_path:
        is_phones_extract = True
        df_extract = df_extract.rename(columns={"trans_id": "id"})
        df_extract['trans_id'] = df_extract['id'].apply(recover_trans_id)
        print(df_extract.columns)
    df_social_info = pandas.read_csv(
        speaker_file_path, encoding='utf-8-sig', header=0)
    df_merged= pandas.merge(
        df_extract,
        df_social_info,
        on='trans_id',
        how='outer', indicator=True)

    # Separate out the rows that did not match
    unmatched_extract = df_merged[df_merged['_merge'] == 'left_only'][['trans_id']].drop_duplicates() # only keep unique trans_id
    unmatched_social_info = df_merged[df_merged['_merge'] == 'right_only'][['trans_id']].drop_duplicates() # only keep unique trans_id

    if not unmatched_extract.empty:
        unmatched_extract.to_csv(unmatched_extract_output_path, index=False, encoding='utf-8-sig')
        print(f"Unmatched rows in extract data written to {unmatched_extract_output_path}")

    if not unmatched_social_info.empty:
        unmatched_social_info.to_csv(unmatched_social_info_output_path, index=False, encoding='utf-8-sig')
        print(f"Unmatched rows in social info data written to {unmatched_social_info_output_path}")

    df_merged.drop(columns=['_merge'], inplace=True)

    df_merged = df_merged.replace('nan', '')

    if is_phones_extract:
        # df_extract = df_extract.drop('trans_id', axis=1)
        # df_extract = df_extract.rename(columns={"id": "trans_id"})
        # print(df_extract.columns)
        df_merged = df_merged.drop('trans_id', axis=1)
        df_merged = df_merged.rename(columns={"id": "trans_id"})
        print(df_extract.columns)

    df_merged.to_csv(extract_output_path, index=False)


def recover_trans_id(id):
    return id.split("_")[0]

if __name__ == '__main__':
    # import the method in the main class
    date = '20240629'
    types = 'noSocialInfo' + '.csv'
    target_var_code = "LEO"
    # TODO: consider use this as the extract type for fomants?
    # 'formant' + '_' + target_var_code
    extract_type = 'clauses'  #
    speakers = ['panel', 'trend']  # ,'style'
    speaker_file_date = "02jun2024"
    working_directory = '/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/'
    for speaker_type in speakers:
        extract_input_path = working_directory + speaker_type + "/extracts/" + 'SWG_' + speaker_type + '_' + extract_type + '_' + date + types
        speaker_file_path = working_directory + speaker_type + "/" + 'SWG_' + speaker_type + '_speakers_' + speaker_file_date + '.csv'  # need to change in case date changes
        extract_output_path = working_directory + speaker_type + "/extracts/" + 'SWG_' + speaker_type + '_' + extract_type + '_' + date + '.csv'
        print(extract_type)
        unmatched_extract_output_path = working_directory + speaker_type + "/extracts/" + 'unmatched_' + 'SWG_' + speaker_type + '_' + extract_type + '_' + date + '.csv'
        unmatched_social_info_output_path = working_directory + speaker_type + "/extracts/" + 'unmatched_' + 'SWG_' + speaker_type + '_speakers_' + speaker_file_date + '.csv'
        add_social_info_to_extracts(extract_input_path, speaker_file_path, extract_output_path, unmatched_extract_output_path, unmatched_social_info_output_path)

        # extract_name = 'SWG_' + speaker_type + '_' + extract_type + '_' + date + types
        # socialInfo_name = 'SWG_' + speaker_type + '_speakers_' + speaker_date + '.csv'  # need to change in case date changes
        # speaker_file_path = common_path + socialInfo_name
        # extracts_input_path_no_info = common_path + extract_name
        # add_social_info_to_extracts(extracts_input_path_no_info, speaker_file_path)  # change names
