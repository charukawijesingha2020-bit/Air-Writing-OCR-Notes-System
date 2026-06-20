import speech_recognition as sr
print('SR OK', getattr(sr, '__version__', 'unknown'))
try:
    names = sr.Microphone.list_microphone_names()
    print('Microphones:')
    for i, n in enumerate(names):
        print(i, n)
except Exception as e:
    print('List error:', type(e).__name__, e)
try:
    with sr.Microphone() as s:
        print('Opened default mic')
except Exception as e:
    print('Open error:', type(e).__name__, e)
