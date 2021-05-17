import numpy as np
import matplotlib.pyplot as plt
import pylab
from scipy.io import wavfile
from scipy import signal
from os import listdir
from os.path import isfile, join
import json
from pymongo import MongoClient
import sys
import multiprocessing
from joblib import Parallel, delayed

def query(hash):
    client = MongoClient('mongodb://192.168.1.46:27017/')
    ##client = MongoClient('mongodb://192.168.159.6:27017/')
    db = client["txazam"]
    collection = db["audiohashes"]
    Q = { "hash": hash['hash'] }
    res= list(collection.find(Q, {'_id': False}))
    return res

#file = './clean/01_Bourgade_samples/01_Bourgade_1.wav'
#file = './noisy_samples/01_Bourgade_samples_noisy/01_Bourgade_4.wav'
audioFiles = [f for f in listdir('test') if isfile(join('test', f))]
for file in audioFiles:
    ## Read file
    file='./test/'+file
    sample_rate, samples = wavfile.read(file)
    ## Convert to mono
    mono=np.average([samples[:,0], samples[:,1]], axis=0)
    ## Normalize (perd massa informació)
    # mono /= np.max(np.abs(mono),axis=0)
    ## Generate spectrogram
    frequencies, times, spectrogram = signal.spectrogram(mono,sample_rate)
    ## Cut frequencies
    # spectrogram=spectrogram[:24,:]
    # frequencies=frequencies[0:24]
    ## Peak thresholds
    A_thres=20000
    T_thres=8000
    ## Horizontal distance to avoid near peaks in the same frequency (197 samples/second)
    N_thres=197*3
    ## The same for the targets
    TS_Thres=197*3 ## 300 ms
    anchorTargetSeconds=3
    anchorsArray=np.array([signal.find_peaks(e, distance = N_thres, height=A_thres)[0] for e in spectrogram])
    targetsArray=np.array([signal.find_peaks(e, distance = TS_Thres, height=T_thres)[0] for e in spectrogram])
    # print([e[0] for e in anchorsArray])
    print('File: {}\nAnchors: {}\tTargets: {}'.format(file, sum([len(e) for e in anchorsArray]), sum([len(e) for e in targetsArray])))

    linkList=[]
    ## For each of 129 frequecies (f) in spectrogram
    for f, _ in enumerate(spectrogram):
        ## For each anchor in the frequecy
        for a in anchorsArray[f]:
            ## loop over all frequecies in the targets
            for targetFreq, ter in enumerate(targetsArray):
                ## for each target in the actual target frequency
                for tps in ter:
                    ## If the target is past time, and not after anchorTargetSeconds add to list
                    if tps > a and tps< a+197*anchorTargetSeconds:
                        linkList.append((f,targetFreq, tps-a))
                    elif tps> a+197*anchorTargetSeconds: continue
    linkDocs=[]
    for e in linkList:
        enter=e[0]
        enter= enter<<8
        enter+=e[1]
        enter=enter<<16
        enter+=e[2]
        enter=enter.item()
        linkDocs.append({'hash': enter, 'name':'{}'.format(file.strip().split('.')[2])})
    ##linkDocs=[{'hash': '{}.{}.{}'.format(e[0], e[1], e[2]), 'name':'{}'.format(file.split('.')[1]).strip()} for e in linkList]
    Result= Parallel(n_jobs=multiprocessing.cpu_count())(delayed(query)(hash) for hash in linkDocs[: len(linkDocs)//2])
    namesList=[]
    countsList=[]
    for z in Result:
        for e in z:
            if e['name'] in namesList:
                countsList[namesList.index(e['name'])]+=1
            else:
                namesList.append(e['name'])
                countsList.append(1)
    tmpList=countsList.copy()
    del tmpList[countsList.index(max(countsList))]
    if max(countsList)<= int(max(tmpList)*1.3):
        print('Checking more hashes')
        Result= Parallel(n_jobs=multiprocessing.cpu_count())(delayed(query)(hash) for hash in linkDocs[len(linkDocs)//2+1 :])
        for z in Result:
            for e in z:
                if e['name'] in namesList:
                    countsList[namesList.index(e['name'])]+=1
                else:
                    namesList.append(e['name'])
                    countsList.append(1)
    print('\nInput name is: {}'.format(str(file.split('.')[1].strip()).strip()))
    print('I think the song is {}'.format(namesList[countsList.index(max(countsList))]))
    del namesList[countsList.index(max(countsList))]
    tmpList=countsList.copy()
    del tmpList[countsList.index(max(countsList))]
    if max(countsList)<= int(max(tmpList)*1.3):
        print('or may be {}'.format(namesList[countsList.index(max(countsList))]))
    print()