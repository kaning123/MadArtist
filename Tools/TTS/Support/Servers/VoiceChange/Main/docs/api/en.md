# MadArtist VoiceChange Default Server Documentation

This server is the default server in the MadArtist VoiceChange project, used to process voice conversion requests and return the converted audio files.

## Port Usage
The server occupies port **5418**.

## API Documentation
The server uses the `rpyc` library and provides the following APIs:

### Func vc_single__
The main voice conversion function.

Definition:
```python
def vc_single__(self,
                input_audio0,
                file_index,
                spk_item : int = 0,
                vc_transform0 : int = 0,
                f0method0 : str = "rmvpe",
                index_rate1 : float = 0.75,
                filter_radius0 : int = 3,
                resample_sr0 : int = 0,
                rms_mix_rate0 : float = 0.25,
                protect0 : float = 0.33,):
        ''':param spk_item: Speaker ID
        :param input_audio0: Path to the input audio file to be processed
        :param vc_transform0: Pitch shift (integer, number of semitones; +12 for one octave up, -12 for one octave down)
        :param f0method0: Pitch extraction algorithm. Use "pm" for singing voices (faster), "harvest" for good bass response but very slow, "crepe" for good quality but GPU-intensive, "rmvpe" for best quality with moderate GPU usage
        :param file_index: Path to the feature retrieval index file
        :param index_rate1: Ratio of retrieved features to use
        :param filter_radius0: If >=3, applies median filtering to harvest pitch detection results; the value is the filter radius. Helps reduce muted/unvoiced artifacts
        :param resample_sr0: Final resampling sample rate after post-processing; 0 means no resampling
        :param rms_mix_rate0: Blending ratio of input source volume envelope to replace output volume envelope. Closer to 1 means more output envelope
        :param protect0: Protects unvoiced consonants and breath sounds to prevent artifacts like electrical distortion. Set to 0.5 to disable; lower values increase protection but may reduce indexing effectiveness
        :return vc_output1: Output info message
        :return vc_output2: Output audio
        '''
```
### Func get_vc
Used to change the output voice for the voice converter.

Definition:
```python
def get_vc(self,
           sid0, 
           protect : float = 0.33):
        ''':param sid0: Target speaker ID for inference
        :param protect: Protects unvoiced consonants and breath sounds to prevent artifacts like electrical distortion. Set to 0.5 to disable; lower values increase protection but may reduce indexing effectiveness
        :return spk_item: Speaker ID
        :return protect: Protection value (same as input)
        :return file_index: Auto-detected index path
        '''