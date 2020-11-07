import pandas


class AddSocialInfo:

    def __init__(self, extract_path, social_info_path):
        self.rootpath = extract_path
        self.sourcepath = social_info_path
        self.phone = False
        self.df_extract = pandas.read_csv(
            extract_path, encoding='utf-8-sig', header=0)
        if "phone" in extract_path or "formant" in extract_path:
            self.phone = True
            self.df_extract = self.df_extract.rename(columns={"trans_id": "id"})
            self.df_extract['trans_id'] = self.df_extract['id'].apply(self.recover_trans_id)
            print(self.df_extract.columns)
        self.df_social_info = pandas.read_csv(
            social_info_path, encoding='utf-8-sig', header=0)

    def read_name(self):
        self.df_extract = pandas.merge(
            self.df_extract,
            self.df_social_info,
            on='trans_id',
            how='outer')
        self.df_extract = self.df_extract.replace('nan', '')
        if self.phone:
            self.df_extract = self.df_extract.drop('trans_id', axis=1)
            self.df_extract = self.df_extract.rename(columns={"id": "trans_id"})
            print(self.df_extract.columns)
        extract_output = 'SWG_'+speaker_type+'_'+extract_type+'_'+date_type[:8]+'.csv'
        self.df_extract.to_csv(
            '/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/'+extract_output,
            index=False)

    def recover_trans_id(self, id):
        return id.split("_")[0]


if __name__ == '__main__':
    # import the method in the main class
    date_type = '20201107' + 'noSocialInfo' + '.csv' #
    extract_type = 'phone'
    speakers = ['panel', 'twin']  #  'trend'
    common_path = '/Users/gaozhuge/Documents/Tuebingen_Uni/hiwi_swg/DDM/'
    for speaker_type in speakers:
        extract_name = 'SWG_'+speaker_type+'_'+extract_type+'_'+date_type
        socialInfo_name = 'SWG_'+speaker_type+'_speakers_24apr2020.csv'  # need to change in case date changes
        social_info_path = common_path + socialInfo_name
        extract_path_no_info = common_path + extract_name
        addSocialInfo = AddSocialInfo(extract_path_no_info, social_info_path)  # change names
        addSocialInfo.read_name()
