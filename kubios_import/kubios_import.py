# -*- coding: utf-8 -*-
"""
Kubios Import & Export
"""

# Imports
import json
import os
import datetime as dt
import numpy as np
import pandas as pd
#---------------------------------------------
#Kubiosレポートからパラメータを抽出
#---------------------------------------------
def import_report(rfile=None, delimiter=',' , sample = 1):
	"""Imports HRV results from a KUBIOS report file in .txt format.

	Parameters
	----------
	rfile : str, file handler
		Absolute filepath or file handler of the KUBIOS report file.
	delimiter : str, character
		Delimiter used in KUBIOS report file.

	Returns
	-------
	results : dict
		Imported parameter values from the KUBIOS report file.

	Raises
	------
	TypeError
		If 'rfile' is not str or file handler.
	IOError
		If provided file does not exist.
	TypeError
		If 'rfile' is not a KUBIOS report file.
	"""



	# Check input
	if type(rfile) is not str and type(rfile) is not file:
		raise TypeError('Unsupported file format. Please provide file path (str) or file handler.')
	elif type(rfile) is str:
		if not os.path.isfile(rfile):
			raise IOError('KUBIOS report file does not exist. Please verify input data.')

	# Check if file is a Kubios export file
	with open(rfile, 'r') as f:
		if 'Kubios HRV' not in f.read():
			raise TypeError("This file does not seem to be a KUBIOS report file.")

	# Load HRV keys
	dir_ = os.path.split(__file__)
	with open(os.path.join(dir_[0], 'keys.json')) as j:
		hrv_parameters = json.load(j)

	# Get non-available parameters
	results = {}
	frequency_arrays = ['fft_peak', 'fft_abs', 'fft_log', 'fft_rel', 'fft_norm', 'ar_peak', 'ar_abs', 'ar_log',
						'ar_norm', 'ar_rel']

	for key in hrv_parameters.keys():
		if 'fft_' in key or 'ar_' in key:
			if key in frequency_arrays:
				results[str(key)] = list()

	# Get available parameters
	with open(rfile, 'r') as f:
		content = f.readlines()


	# Get data
	for line in content:
		line = line.split(delimiter)
		for key, label in hrv_parameters.items():
			if type(label) is str:
				if str(label) in line[0]:
					index = sample+1 if key in ['ar_total', 'ar_ratio'] else (sample if len(line) > sample else 0)
					try:
						val = float(line[index].lstrip())
					except ValueError:
						val = str(line[index]).rstrip().lstrip().replace('\n', '').replace('\r', '')
						if key in ['interpolation', 'ar_model', 'fft_window', 'fft_overlap', 'fft_grid', 'threshold']:
							val = float(''.join(i for i in val if i.isdigit()))
					results[str(key)] = val if not line[index].isspace() else 'n/a'
			else:
				for l in label:
					if str(l) == line[0].rstrip().lstrip().replace(':', ''):
						index = sample if 'fft_' in key else sample+1
						val = float(line[index].lstrip()) if not line[index].isspace() else 'n/a'
						results[str(key)].append(val)
	return results

#---------------------------------------------
#各セグメントごとにレポートを作成
#---------------------------------------------
def segment_report(rfile=None, delimiter=',',labels= ["Contentment","Neutral","Disgust"],segments = 3):
    #ラベル数がセグメント番号と一致しない場合にエラー
    if len(labels) != segments:
        return False
    for i in range(segments):
        segment_id = 1 + 2 * i

        #各セグメントのパラメータ一覧を取得
        report = import_report(rfile,sample=segment_id)
        
        #心拍パラメータ一覧を取得
        segment_hrv_report = modify_list_to_float(report,labels[i])
        
        #アンケート情報を取得
        que_fname = r"C:\Users\akito\Desktop\Hashimoto\summary\question_naire\sum_question_naire.xlsx"
        segment_question_report = get_QuestioNaire(que_fname,segment_hrv_report)

        if i == 0:
           report_df = pd.DataFrame([], columns=segment_hrv_report.keys())
        report_df =  pd.concat([report_df, pd.DataFrame(segment_hrv_report , index=[i])])

    return report_df
    pass


#---------------------------------------------
#パラメータリストをfloat型に変換する
#---------------------------------------------
def modify_list_to_float(parameter_list,emotion = "None"):
    #-------------------------------------------------
    #・パラメータがlist型の場合
    #ar_rel : [A B C]を
    #ar_rel_vlf : A, ar_rel_lf : B, ar_rel_vhf : C
    #に変換
    #※パラメータがfloat型の場合はそのまんま
    #-------------------------------------------------
    results = {'emotion' : emotion }
    for key in parameter_list.keys():
        if type(parameter_list[key]) == list:
            #変更するラベル名を定義
            if len(parameter_list[key]) == 2:  labels = ['lf','hf']
            elif len(parameter_list[key]) == 3:labels = ['vlf','lf','hf']

            for (list_item,label) in zip(parameter_list[key],labels):
                #dict名をkey + vlf or lf or hfに変更する
                results[key + '_' + label] = list_item
        else:
            if key == 'Filename':
                #ファイル名からに日にちとユーザ名を取得
                results['date'], results['user'] = fileName_Info(parameter_list[key])

            results[key] = parameter_list[key]
    return results



#---------------------------------------------
#アンケート一覧と心拍パラメータを組み合わせる
#---------------------------------------------
def get_QuestioNaire(fname,hrv_report):
    df = pd.read_excel(fname)
    print(hrv_report['user'])
    print(hrv_report['date'])
    print(hrv_report['emotion'])
    df_item = df[
       # (df['date'] == hrv_report['date']) &
       #(df['user'] == hrv_report['user']) &
       #(df['Emotion'] == hrv_report['emotion'])
       (df['date'] == hrv_report['date']) &
       (df['user'] ==  hrv_report['user']) &
       (df['Emotion'] == hrv_report['emotion'])
       ]
    return df_item
    pass


#---------------------------------------------
#ファイル名からuser名と日にちを取得する
#---------------------------------------------
def fileName_Info(file_name):
    import re #reモジュールのインポート
    #日付を取得
    date = re.sub("\\D", "", file_name)
    #USER名を取得
    user = file_name[file_name.find('RRI_')+ 4 : file_name.find('.csv')]
    return date , user


if __name__ == "__main__":
    questionNaire = r"C:\Users\akito\Desktop\Hashimoto\summary\question_naire\sum_question_naire.xlsx"
    path = r"C:\Users\akito\Desktop\RRI_kishida_hrv.txt"
    A = segment_report(path)
    A.to_excel(r"C:\Users\akito\Desktop\test.xlsx")

    B = get_QuestioNaire(questionNaire ,A)

    #results = import_report(path,sample = 5);
    #results = modify_list_to_float(results,"Neutral");
    #for key in results.keys():
    #    print(key, results[key]);
    pass