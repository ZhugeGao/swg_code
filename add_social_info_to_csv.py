import pandas


class AddSocialInfo:

    def __init__(self, extract_path, social_info_path):
        self.rootpath = extract_path
        self.sourcepath = social_info_path

        self.df_extract = pandas.read_csv(
            extract_path, encoding='utf-8-sig', header=0)
        self.df_social_info = pandas.read_csv(
            social_info_path, encoding='utf-8-sig', header=0)

    def read_name(self):
        # self.df_extract.astype(str)
        # self.df_social_info.astype(str)
        self.df_extract = pandas.merge(
            self.df_extract,
            self.df_social_info,
            on='trans_id',
            how='outer')
        self.df_extract = self.df_extract.replace('nan', '')
        extract_output = 'SWG_'+speaker_type+'_'+extract_type+'_'+date_type[:8]+'.csv'
        self.df_extract.to_csv(
            '/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/'+extract_output,
            index=False)


if __name__ == '__main__':
    date_type = '20200408' + 'noSocialInfo' + '.csv'
    extract_type = 'words'
    speakers = ['twin', 'trend', 'panel']
    common_path = '/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/'
    for speaker_type in speakers:
        extract_name = 'SWG_'+speaker_type+'_'+extract_type+'_'+date_type
        socialInfo_name = 'swg_'+speaker_type+'_speakers_09mar2020.csv'  # need to change in case date changes
        social_info_path = common_path + socialInfo_name
        extract_path_no_info = common_path + extract_name
        addSocialInfo = AddSocialInfo(extract_path_no_info, social_info_path)  # change names
        addSocialInfo.read_name()
