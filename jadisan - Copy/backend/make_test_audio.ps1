Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.SetOutputToWaveFile('test_complaint.wav')
$synth.Speak('There is a large pothole near the Gandhi statue on Anna Salai. Water is leaking from the road and causing accidents for two wheelers.')
$synth.Dispose()
Write-Host 'WAV created'
