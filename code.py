import numpy as np
import matplotlib.pyplot as plt
import pylab
from scipy.io import wavfile
from scipy import signal
from os import listdir
from os.path import isfile, join
import json
import sys
from pymongo import MongoClient
import multiprocessing
from joblib import Parallel, delayed

def saveHashes(file):
    #db = TinyDB('./db.json')
    client = MongoClient('mongodb://192.168.1.46:27017/')
    #client = MongoClient('mongodb://192.168.159.6:27017/')
    db = client["txazam"]
    collection = db["audiohashes"]

    file = './inputs/'+file
    ## Read file
    sample_rate, samples = wavfile.read(file)
    ## Convert to mono
    mono=np.average([samples[:,0], samples[:,1]], axis=0)
    ## Normalize
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
    print('File: {}\nAnchors: {}\tTargets: {}'.format(str(file.strip().split('.')[2]).strip(), sum([len(e) for e in anchorsArray]), sum([len(e) for e in targetsArray])))

    linkList=set()
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
                        linkList.add((f,targetFreq, tps-a))
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
    print('Added: {}'.format(str(file.strip().split('.')[2]).strip()))

    ####linkDocs=[{'hash': '{}.{}.{}'.format(e[0], e[1], e[2]), 'name':'{}'.format(file.strip().split('.')[2])} for e in linkList]
    
    collection.insert_many(linkDocs)

audioFiles = [f for f in listdir('inputs') if isfile(join('inputs', f))]
Parallel(n_jobs=multiprocessing.cpu_count())(delayed(saveHashes)(file) for file in audioFiles)

