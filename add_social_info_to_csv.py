import pandas


def add_social_info_to_extracts(extract_input_path, speaker_file_path, extract_output_path, is_phones_extract=False):
    df_extract = pandas.read_csv(
        extract_input_path, encoding='utf-8-sig', header=0)
    if "phone" in extract_input_path or "formant" in extract_input_path:
        is_phones_extract = True
        df_extract = df_extract.rename(columns={"trans_id": "id"})
        df_extract['trans_id'] = df_extract['id'].apply(recover_trans_id)
        print(df_extract.columns)
    df_social_info = pandas.read_csv(
        speaker_file_path, encoding='utf-8-sig', header=0)
    df_extract = pandas.merge(
        df_extract,
        df_social_info,
        on='trans_id',
        how='outer')
    df_extract = df_extract.replace('nan', '')
    if is_phones_extract:
        df_extract = df_extract.drop('trans_id', axis=1)
        df_extract = df_extract.rename(columns={"id": "trans_id"})
        print(df_extract.columns)

    df_extract.to_csv(extract_output_path, index=False)


def recover_trans_id(id):
    return id.split("_")[0]


# TODO: run this in SWG_main
if __name__ == '__main__':
    # import the method in the main class
    date = '20220310'
    types = 'noSocialInfo' + '.csv'
    target_var_code = "LEO"
    # TODO: consider use this as the extract type for fomants?
    # 'formant' + '_' + target_var_code
    extract_type = 'phones'  #
    speakers = ['panel']  # 'trend','twin',   ,'style'
    speaker_date = '30may2021'
    common_path = '/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/'
    for speaker_type in speakers:
        extract_name = 'SWG_' + speaker_type + '_' + extract_type + '_' + date + types
        socialInfo_name = 'SWG_' + speaker_type + '_speakers_' + speaker_date + '.csv'  # need to change in case date changes
        speaker_file_path = common_path + socialInfo_name
        extracts_input_path_no_info = common_path + extract_name
        add_social_info_to_extracts(extracts_input_path_no_info, speaker_file_path)  # change names
