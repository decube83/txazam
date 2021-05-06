import numpy as np
import matplotlib.pyplot as plt
import pylab
from scipy.io import wavfile
from scipy.fftpack import fft
from scipy import signal

cut_threshold= 10000
#myAudio = './library1/19. Annalise.wav'
myAudio = './library1/18. Dog_Soldier_Stand_Down.wav'
# #"./library1/18. Dog_Soldier_Stand_Down.wav"

#Read file and get sampling freq [ usually 44100 Hz ]  and sound object
samplingFreq, mySound = wavfile.read(myAudio)

#Check if wave file is 16bit or 32 bit. 24bit is not supported
mySoundDataType = mySound.dtype

#We can convert our sound array to floating point values ranging from -1 to 1 as follows
mySoundShape = mySound.shape
print('Shape is: {}'.format(mySoundShape))
print('samplig freq is is: {}'.format(samplingFreq))
## Assign chanels
L= mySound[:,0]
R= mySound[:,1]
del mySound
## Convert to mono averaging both arrays
mono=np.average([L, R], axis=0)
del L
del R
## Threshold it
# mono[mono<cut_threshold]=0
## normalize it
mono /= np.max(np.abs(mono),axis=0)
## Create spectrogram
frequencies, times, spectrogram = signal.spectrogram(mono, samplingFreq)
## Limit to first 24 frequencies (4KHz aprox)
spectrogram=spectrogram[:24,:]
frequencies=frequencies[0:24]
# print(spectrogram.shape)
# print(times)

plt.pcolormesh(times, frequencies, spectrogram)

# plt.imshow(spectrogram)

# # plt.ylabel('Frequency [Hz]')

# # plt.xlabel('Time [sec]')

plt.show()
exit()
#mySound = mySound / (2.**15)

#Check sample points and sound channel for duel channel(5060, 2) or  (5060, ) for mono channel

